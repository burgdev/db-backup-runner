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
    """Base BackupProvider class"""

    name: str = None  # type: ignore
    """Backup provider name (e.g. postgres)"""
    default_dump_binary: str | None = None
    """Default dump binary"""
    default_dump_args: str | None = None
    """Default dump binary arguments"""
    default_restore_binary: str | None = "RESTORE_COMMAND"
    """Default restore binary"""
    default_restore_args: str | None = ""
    """Default restore binary arguments"""
    min_file_size: int = 200
    """Maximum file size, used to validate the generated file"""
    pattern: str | None = None
    """Pattern which is checked in the dumped file"""
    plain_file_extension: str = ".sql"
    """File extenstion used for the dumped file"""

    def __init__(
        self, container: Container, compression: CompressionAlgorithm | None = None
    ):
        """Backup provider constructor

        Args:
          container: Container object
          compression: Compression algorithm
        """
        self.compression: CompressionAlgorithm | None = compression
        """Compression algorithm"""
        if self.name is None:
            raise AttributeError("Add 'name' to your BackupProvider.")
        self.container: Container = container
        """Container object"""

    def dump(self) -> str:
        """Dump database"""
        raise NotImplementedError("Dump method must be implemented by subclass")

    def restore(self, backup_file: Path) -> None:
        """Restore database"""
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
        """Checks if container supports a backup provider"""
        provider_name = self.get_container_label("backup_provider")
        if provider_name and provider_name == self.name:
            return True
        if not self.get_dump_binary():
            return False
        if self.binary_exists_in_container(self.get_dump_binary()):
            return True
        return False

    def validate_file(self, file_path: Path) -> bool:
        """Validate the generated file"""
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
        """Trigger webhook.

        Args:
          message: Message send to the webhook
          address: If not set taken from the label
          code: Code which is sent to the webhook
          append: Path appended to address (can be used for fails)
        """
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
                    "code": code,
                },
            )
        except requests.RequestException as e:
            logger.error(f"Failed to call webhook: {e}")

    def trigger_error_webhook(self, message: str, address: str, code: int = 1) -> None:
        """Triggers an error on the webhook. `code` is appended to the address."""
        self.trigger_webhook(
            message=message, address=f"{address}", code=code, append=str(code)
        )

    def trigger_success_webhook(
        self, message: str, address: str, code: int = 0
    ) -> None:
        """Triggers an success on the webhook."""
        self.trigger_webhook(message=message, address=f"{address}", code=code)

    def get_dump_binary(self) -> str:
        """Get the binary used to dump the backup."""
        return self.get_container_label("dump_binary", self.default_dump_binary) or ""

    def get_dump_args(self) -> str:
        """Arguments for the dump binary."""
        return self.get_container_label("dump_args", self.default_dump_args) or ""

    def get_restore_binary(self) -> str:
        """Get the binary used to restore the backup."""
        return (
            self.get_container_label("restore_binary", self.default_restore_binary)
            or ""
        )

    def get_restore_args(self) -> str:
        """Arguments for the restore binary."""
        return self.get_container_label("restore_args", self.default_restore_args) or ""

    def get_container_env(self) -> dict[str, str | None]:
        """Get environment variables from container."""
        _, (env_output, _) = self.container.exec_run("env", demux=True)
        return dict(dotenv_values(stream=StringIO(env_output.decode())))

    def binary_exists_in_container(self, binary_name: str) -> bool:
        """Check if binary exists inside the container."""
        exit_code, _ = self.container.exec_run(["which", binary_name])
        return exit_code == 0

    def get_container_label(self, label: str, default: str | None = None) -> str | None:
        """Get labels for container."""
        labels = self.container.labels or {}
        for key, value in labels.items():
            full_label = "db-backup-runner." + label
            if key.lower() == full_label.lower():
                return value
        return default

    def get_service_name(self) -> str:
        """Get service name (only if started with docker compose)."""
        labels = self.container.labels or {}
        return labels.get("com.docker.compose.service", "")
