from io import StringIO
from pathlib import Path
import socket

import click
from docker.models.containers import Container
from dotenv import dotenv_values
from loguru import logger
import requests


from db_backup_runner.types import CompressionAlgorithm


class BackupProviderBase:
    name: str = None  # type: ignore
    default_dump_binary: str | None = None
    default_dump_args: str | None = None
    default_restore_binary: str | None = "RESTORE_COMMAND"
    default_restore_args: str | None = ""
    min_file_size: int = 200
    pattern: str | None = None
    plain_file_extension: str = ".sql"

    def __init__(
        self, container: Container, compression: CompressionAlgorithm | None = None
    ):
        self.compression = compression
        if self.name is None:
            raise AttributeError("Add 'name' to your BackupProvider.")
        self.container = container

    def dump(self) -> str:
        raise NotImplementedError("Dump method must be implemented by subclass")

    def restore(self, backup_file: Path) -> None:
        service_name = self.get_service_name()
        dump_file = f"/tmp/db{self.plain_file_extension}"
        if service_name:
            main_command = "docker compose"
            target_name = service_name
        else:
            main_command = "docker"
            target_name = self.container.name
        logger.warning("Run the following commands to restore your backup.")
        logger.warning("Make sure to check the script and replace variables if needed!")
        click.secho(
            "-----------------------------------------------------------------------------",
            dim=True,
            err=True,
        )
        click.secho("#!/bin/sh", dim=True)
        click.secho(
            f"# Restore {'service' if service_name else 'container'} '{click.style(target_name,bold=True, fg='green')}'",
            dim=True,
        )
        click.secho(
            f"# copy file from host ({socket.gethostname()}) to container '{target_name}' ({self.container.short_id})",
            dim=True,
        )
        click.secho(f"{main_command} cp {backup_file} {target_name}:{dump_file}")
        click.secho(
            f"# run restore command for '{self.name}' backup provider", dim=True
        )
        click.echo(
            f"{main_command} exec {target_name} {self.get_restore_binary()} {self.get_restore_args()} {dump_file}"
        )
        click.secho(
            "-----------------------------------------------------------------------------",
            dim=True,
            err=True,
        )
        click.echo("")

    def is_backup_provider(self) -> bool:
        provider_name = self.get_container_label("backup_provider")
        if provider_name and provider_name == self.name:
            return True
        if not self.get_dump_binary():
            return False
        if self.binary_exists_in_container(self.get_dump_binary()):
            return True
        return False

    def validate_file(self, file_path: Path) -> bool:
        min_file_size = int(
            self.get_container_label("min_file_size") or self.min_file_size
        )
        file_size = file_path.stat().st_size
        if file_size < min_file_size:
            logger.error(
                f"Backup file {file_path} size ({file_size} bytes) is smaller than the minimum size of {min_file_size} bytes."
            )
            return False

        pattern = self.get_container_label("pattern", self.pattern)
        if pattern:
            with open(file_path, "r") as file:
                try:
                    for line in file:
                        if pattern in line:
                            return True
                except UnicodeDecodeError:
                    logger.error("Binary file, cannot check for pattern.")
                    return True

            logger.error(
                f"Backup file {file_path} does not contain predefined SQL dump patterns."
            )
            return False

        return True

    def trigger_webhook(
        self, message: str, address: str, code: int = 0, append: str = ""
    ) -> None:
        """A code of '0' means success."""
        address = self.get_container_label("webhook") or address
        if address.lower() == "none":
            logger.debug(f"Webhook address is disabled for '{self.container.name}'.")
            return
        if not address:
            logger.debug(
                f"Would send heartbeat with code '{code}' but no address is defined."
            )
            return
        try:
            address = address if not append else f"{address}/{append}"
            logger.debug(f"Send heartbeat to '{address}' with code '{code}'.")
            requests.post(
                f"{address}",
                json={
                    "message": message,
                    "container": self.container.name,
                    "provider": self.name,
                    "code": 0,
                },
            )
        except requests.RequestException as e:
            logger.error(f"Failed to call webhook: {e}")

    def trigger_error_webhook(self, message: str, address: str, code: int = 1) -> None:
        self.trigger_webhook(
            message=message, address=f"{address}", code=code, append=str(code)
        )

    def trigger_success_webhook(
        self, message: str, address: str, code: int = 0
    ) -> None:
        self.trigger_webhook(message=message, address=f"{address}", code=code)

    def get_dump_binary(self) -> str:
        return self.get_container_label("dump_binary", self.default_dump_binary) or ""

    def get_dump_args(self) -> str:
        return self.get_container_label("dump_args", self.default_dump_args) or ""

    def get_restore_binary(self) -> str:
        return (
            self.get_container_label("restore_binary", self.default_restore_binary)
            or ""
        )

    def get_restore_args(self) -> str:
        return self.get_container_label("restore_args", self.default_restore_args) or ""

    def get_container_env(self) -> dict[str, str | None]:
        _, (env_output, _) = self.container.exec_run("env", demux=True)
        return dict(dotenv_values(stream=StringIO(env_output.decode())))

    def binary_exists_in_container(self, binary_name: str) -> bool:
        exit_code, _ = self.container.exec_run(["which", binary_name])
        return exit_code == 0

    def get_container_label(self, label: str, default: str | None = None) -> str | None:
        labels = self.container.labels or {}
        for key, value in labels.items():
            full_label = "db-backup-runner." + label
            if key.lower() == full_label.lower():
                return value
        return default

    def get_service_name(self) -> str:
        labels = self.container.labels or {}
        return labels.get("com.docker.compose.service", "")
