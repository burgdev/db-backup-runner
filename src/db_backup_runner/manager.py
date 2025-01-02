"""Main module which manages the backups and restore functions"""

import secrets
from loguru import logger
from docker.errors import DockerException
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import docker
import pycron
from docker.models.containers import Container
from tqdm.auto import tqdm

import socket
from db_backup_runner.provider import BACKUP_PROVIDERS, BackupProviderBase
from db_backup_runner.utils import (
    DEFAULT_BACKUP_DIR,
    get_compressed_file_extension,
    open_file_compressed,
)

from db_backup_runner.types import CompressionAlgorithm


class BackupManager:
    """Manages the backups and restore functions"""

    BACKUP_PROVIDERS: list[type[BackupProviderBase]] = BACKUP_PROVIDERS

    def __init__(
        self,
        compression: CompressionAlgorithm = "plain",
        backup_dir: Path = DEFAULT_BACKUP_DIR,
        use_timestamp: bool = False,
        use_secret: bool = False,
        webhook_url: str = "",
        project_name: str = "",
        global_mode: bool = False,
    ):
        self.compression: CompressionAlgorithm = compression
        self.backup_dir = backup_dir
        self.use_timestamp = use_timestamp
        self.strtimestamp: str = (
            datetime.now().strftime("%Y%m%d%H%M%S") if self.use_timestamp else ""
        )
        self.use_secret = use_secret
        self.webhook_url = webhook_url
        self.global_mode = global_mode
        self.porject_name = project_name
        try:
            self.docker_client = docker.from_env()
        except DockerException:
            logger.error(
                "Docker socket is missing, add the following volume: '/var/run/docker.sock:/var/run/docker.sock:ro'"
            )
            sys.exit(1)

    def get_temp_backup_file_name(self, provider: BackupProviderBase) -> str:
        timestamp = f"-{self.strtimestamp}" if self.use_timestamp else ""
        secret = f"-{secrets.token_hex(4)}" if self.use_secret else ""
        return f".auto-backup{timestamp}{secret}{provider.plain_file_extension}"

    def get_backup_filename(
        self, container: Container, provider: BackupProviderBase
    ) -> Path:
        timestamp = f"-{self.strtimestamp}" if self.use_timestamp else ""
        name = Path(
            f"{container.name}.{provider.name.lower()}{timestamp}{get_compressed_file_extension(self.compression)}"
        )
        if self.compression == "plain":
            return name.with_suffix(provider.plain_file_extension)
        return name

    def get_my_container_id(self):
        return socket.gethostname()

    def get_compose_project(self):
        if self.global_mode:
            return None
        if self.porject_name:
            return self.porject_name
        my_id = self.get_my_container_id()
        logger.debug(f"Looking for my container with id '{my_id}'")
        containers = self.docker_client.containers.list(filters={"id": my_id})
        if len(containers) == 0:
            logger.debug(f"Could not find any container with id '{my_id}'")
        else:
            container = containers[0]
            logger.debug(f"Found the container named '{container.name}'")
            labels = container.labels or {}
            if "com.docker.compose.project" in labels:
                project_name = labels["com.docker.compose.project"]
                logger.info(
                    f"Found the project name from docker compose label '{project_name}'"
                )
                return project_name
        project_name = Path().cwd().name
        logger.info(f"Use the project name from current directory '{project_name}'")
        if project_name:
            return project_name
        logger.error(
            "Could not find the project name, use '--compose NAME' or '--global' flag."
        )
        return None

    def get_enabled_containers(self) -> Iterable[Container]:
        enable_filters = {"label": "db-backup-runner.enable=true"}
        enabled_containers = self.docker_client.containers.list(filters=enable_filters)
        logger.trace(
            f"Enabled containers: {', '.join([str(c.name) for c in enabled_containers])}."
        )
        project_containers = []
        project_name = self.get_compose_project()
        if project_name is not None and not self.global_mode:
            project_filters = {"label": f"com.docker.compose.project={project_name}"}
            project_containers = self.docker_client.containers.list(
                filters=project_filters
            )
            logger.trace(
                f"Project containers: {', '.join([str(c.name) for c in project_containers])}."
            )

        containers = (
            enabled_containers
            if self.global_mode
            else list(set(enabled_containers) & set(project_containers))
        )
        if len(containers) == 0:
            logger.error(
                "No containers found, did you add the label 'db-backup-runner.enable=true'?"
            )
            if not self.global_mode:
                logger.error(
                    f"No containers found for project '{project_name}', use '--project NAME' or '--global' flag."
                )
            else:
                logger.info("You are running in '--global' mode.")
            sys.exit(1)

        return containers

    def get_backup_provider(self, container: Container) -> Optional[BackupProviderBase]:
        for provider_cls in self.BACKUP_PROVIDERS:
            tmp_prov = provider_cls(container, compression=self.compression)
            if tmp_prov.is_backup_provider():
                return tmp_prov

        logger.error(
            f"Could not find backup provider for container '{container.name}'."
        )
        return None

    def backup(self, now: datetime) -> int:
        logger.info("Starting backup...")
        containers = self.get_enabled_containers()
        logger.info(f"Found {len(list(containers))} containers.")
        logger.debug(f"Containers: {', '.join([str(c.name) for c in containers])}.")

        backed_up_containers = []
        fails = 0
        for container in containers:
            provider = self.get_backup_provider(container)
            if provider is None:
                continue

            container_backup_dir = (
                self.backup_dir / container.name if container.name else self.backup_dir
            )
            container_backup_dir.mkdir(parents=True, exist_ok=True)
            backup_filename = self.get_backup_filename(
                container=container, provider=provider
            )
            backup_filepath = container_backup_dir / backup_filename
            backup_temp_file_path = (
                container_backup_dir / self.get_temp_backup_file_name(provider=provider)
            )

            backup_command = provider.dump()
            logger.info(f"Run backup command: '{backup_command}'")
            stderr, output = container.exec_run(backup_command, stream=True, demux=True)

            logger.info(
                f"Backing up container '{container.name}' with '{provider.name}' backup provider:"
            )
            stderr_messages = []
            with open_file_compressed(
                backup_temp_file_path, self.compression
            ) as backup_temp_file:
                with tqdm.wrapattr(
                    backup_temp_file,
                    method="write",
                    desc=f"      {backup_filename}",
                    disable=not sys.stdout.isatty,
                ) as f:
                    for stdout, stderr in output:
                        if stderr:
                            stderr_messages += stderr.decode().strip().split("\n")
                        if stdout is None:
                            continue
                        f.write(stdout)
            for stderr in stderr_messages:
                logger.warning(stderr)

            if provider.validate_file(backup_temp_file_path):
                os.replace(backup_temp_file_path, backup_filepath)
                logger.info(
                    f"Backup complete: '{backup_filepath}' (path from inside the container!)"
                )
                if fails == 0:
                    # if any fail occured we do not trigger any heartbeat anymore
                    provider.trigger_success_webhook(
                        f"Backup of container '{container.name}' successful.",
                        address=self.webhook_url,
                    )
            else:
                provider.trigger_error_webhook(
                    f"Backup of container '{container.name}' failed.",
                    address=self.webhook_url,
                )
                fails += 1

            backed_up_containers.append(container.name)

        duration = (datetime.now() - now).total_seconds()
        logger.info(
            f"Backup of {len(backed_up_containers)} containers complete in {duration:.2f} seconds."
        )
        return fails

    def restore(self, target: str, restore_file: Path) -> int:
        containers = self.get_enabled_containers()
        for container in containers:
            if target and target in [container.name, container.short_id, container.id]:
                continue
            provider = self.get_backup_provider(container)
            if not provider:
                logger.error(
                    f"No backup provider found for container {container.name}."
                )
                return 0
            if target and target == provider.get_service_name():
                continue
            provider.restore(restore_file)
        logger.info("You can pipe the output into a file and run the script")
        return 0


if __name__ == "__main__":
    # Configure logger to use a custom format
    logger.remove()  # Remove the default handler
    logger.add(sys.stdout, format="<level>{level}: {message}</level>", level="DEBUG")
    _manager = BackupManager()
    if os.environ.get("DB_BACKUP_CRON"):
        logger.info(
            f"Running backup with schedule '{os.environ.get('DB_BACKUP_CRON')}'."
        )
        pycron.start()
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) != 4:
            logger.error(
                "Usage: python script.py restore <container_name> <backup_file>"
            )
        else:
            _manager.restore(sys.argv[2], Path(sys.argv[3]))
    else:
        _manager.backup(datetime.now())
