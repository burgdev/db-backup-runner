from pathlib import Path
from loguru import logger
import click
import sys
from datetime import datetime

import pycron
from db_backup_runner.manager import BackupManager
from db_backup_runner.utils import DEFAULT_BACKUP_DIR, compression_algorithms


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def cli(verbose):
    # Configure logger to use a custom format
    logger.remove()  # Remove the default handler
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stdout, format="<level>{level}: {message}</level>", level=log_level)


def compression_option():
    return click.option(
        "-c",
        "--compression",
        help="Compression algorithm.",
        envvar="COMPRESSION",
        type=click.Choice(compression_algorithms),
        show_default=True,
        default="plain",
    )


def backup_dir_option():
    return click.option(
        "-b",
        "--backup-dir",
        help="Backup directory.",
        envvar="BACKUP_DIR",
        show_default=True,
        default=DEFAULT_BACKUP_DIR,
    )


def use_timestamp_option():
    return click.option(
        "-t",
        "--use-timestamp",
        help="Add a timestamp to the backup filename.",
        envvar="USE_TIMESTAMP",
        is_flag=True,
        show_default=True,
    )


def webhook_option():
    return click.option(
        "-w",
        "--webhook",
        help="Heartbeat webhook address.",
        envvar="WEBHOOK",
        default="",
    )


@cli.command()
@click.option(
    "-s",
    "--schedule",
    help="Cron schedule (https://crontab.guru), per default it runs at 2am every day.",
    envvar="SCHEDULE",
    show_default=True,
    default="0 2 * * *",
)
@click.option(
    "-o",
    "--on-startup",
    is_flag=True,
    help="Run backup on startup as well.",
    envvar="ON_STARTUP",
    type=bool,
)
@compression_option()
@backup_dir_option()
@use_timestamp_option()
@webhook_option()
def scheduled_backup(
    schedule, on_startup, compression, backup_dir, use_timestamp, webhook
):
    "Run backup based on the schedule."
    manager = BackupManager(
        compression=compression,
        backup_dir=Path(backup_dir),
        use_timestamp=use_timestamp,
        webhook_url=webhook,
    )
    if on_startup:
        logger.info("Running backup on startup.")
        manager.backup(datetime.now())
    logger.info(f"Running backup with schedule '{schedule}'.")
    pycron.cron(schedule)(manager.backup)  # type: ignore
    pycron.start()


@cli.command()
@compression_option()
@backup_dir_option()
@use_timestamp_option()
@webhook_option()
def backup(compression, backup_dir, use_timestamp, webhook):
    "Run a manual backup."
    manager = BackupManager(
        compression=compression,
        backup_dir=Path(backup_dir),
        use_timestamp=use_timestamp,
        webhook_url=webhook,
    )
    sys.exit(manager.backup(datetime.now()))


@cli.command()
@click.argument("container_name")
@click.argument("backup_file", type=click.Path(exists=True))
def restore(container_name, backup_file):
    "Restore a backup for a specific container."
    manager = BackupManager()
    manager.restore(container_name, Path(backup_file))


if __name__ == "__main__":
    cli()
