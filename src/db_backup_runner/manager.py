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

from db_backup_runner.provider import BACKUP_PROVIDERS, BackupProviderBase
from db_backup_runner.utils import (
    DEFAULT_BACKUP_DIR,
    get_compressed_file_extension,
    open_file_compressed,
)

from db_backup_runner.types import CompressionAlgorithm


class BackupManager:
    BACKUP_PROVIDERS: list[type[BackupProviderBase]] = BACKUP_PROVIDERS

    def __init__(
        self,
        compression: CompressionAlgorithm = "plain",
        backup_dir: Path = DEFAULT_BACKUP_DIR,
        use_timestamp: bool = False,
        use_secret: bool = False,
        webhook_url: str = "",
    ):
        self.compression: CompressionAlgorithm = compression
        self.backup_dir = backup_dir
        self.use_timestamp = use_timestamp
        self.strtimestamp: str = (
            datetime.now().strftime("%Y%m%d%H%M%S") if self.use_timestamp else ""
        )
        self.use_secret = use_secret
        self.webhook_url = webhook_url
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
            f"{container.name}.{provider.name.lower()}{timestamp}{provider.plain_file_extension}{get_compressed_file_extension(self.compression)}"
        )
        if self.compression == "plain":
            return name.with_suffix(provider.plain_file_extension)
        return name

    def get_enabled_containers(self) -> Iterable[Container]:
        filters = {"label": "db-backup-runner.enable=true"}
        return self.docker_client.containers.list(filters=filters)

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
            _, output = container.exec_run(backup_command, stream=True, demux=True)

            logger.info(
                f"Backing up container '{container.name}' with '{provider.name}' backup provider:"
            )
            with open_file_compressed(
                backup_temp_file_path, self.compression
            ) as backup_temp_file:
                with tqdm.wrapattr(
                    backup_temp_file,
                    method="write",
                    desc=f"      {backup_filename}",
                    disable=not sys.stdout.isatty,
                ) as f:
                    for stdout, _ in output:
                        if stdout is None:
                            continue
                        f.write(stdout)

            if provider.validate_file(backup_temp_file_path):
                os.replace(backup_temp_file_path, backup_filepath)
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

    def restore(self, container_name: str, backup_file: Path) -> int:
        container = self.docker_client.containers.get(container_name)
        provider = self.get_backup_provider(container)
        if not provider:
            logger.error(f"No backup provider found for container {container_name}.")
            return 0

        logger.info(
            f"Restoring backup for container {container_name} from {backup_file}."
        )
        provider.restore(backup_file)
        return 0


if __name__ == "__main__":
    # Configure logger to use a custom format
    logger.remove()  # Remove the default handler
    logger.add(sys.stdout, format="<level>{level}: {message}</level>", level="DEBUG")
    manager = BackupManager()
    if os.environ.get("SCHEDULE"):
        logger.info(f"Running backup with schedule '{os.environ.get('SCHEDULE')}'.")
        pycron.start()
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) != 4:
            logger.error(
                "Usage: python script.py restore <container_name> <backup_file>"
            )
        else:
            manager.restore(sys.argv[2], Path(sys.argv[3]))
    else:
        manager.backup(datetime.now())
