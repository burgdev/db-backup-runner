"""Command line interface, see also [cli help](https://burgdev.github.io/db-backup-runner/cli/)."""

from pathlib import Path
from loguru import logger
import click
import sys
from datetime import datetime

import pycron
from db_backup_runner.manager import BackupManager
from db_backup_runner.utils import DEFAULT_BACKUP_DIR, compression_algorithms


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose output.",
    envvar="DB_BACKUP_VERBOSE",
    show_envvar=True,
)
def cli(verbose):
    "Main command to backup and restore databases."
    # Configure logger to use a custom format
    logger.remove()  # Remove the default handler
    log_level = "INFO"
    if verbose > 0:
        log_level = "DEBUG"
    if verbose > 1:
        log_level = "TRACE"

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</> {message}",
        level=log_level,
    )
    logger.trace("Setup logging with trace level.")


def _compression_option():
    return click.option(
        "-c",
        "--compression",
        help="Compression algorithm.",
        envvar="COMPRESSION",
        type=click.Choice(compression_algorithms),
        show_default=True,
        show_envvar=True,
        default="plain",
    )


def _backup_dir_option():
    return click.option(
        "-b",
        "--backup-dir",
        help="Backup directory.",
        envvar="BACKUP_DIR",
        show_default=True,
        show_envvar=True,
        default=DEFAULT_BACKUP_DIR,
    )


def _use_timestamp_option():
    return click.option(
        "-t",
        "--use-timestamp",
        help="Add a timestamp to the backup filename.",
        envvar="USE_TIMESTAMP",
        show_envvar=True,
        is_flag=True,
        show_default=True,
    )


def _webhook_option():
    return click.option(
        "-w",
        "--webhook",
        "webhook_url",
        help="Heartbeat webhook address.",
        envvar="WEBHOOK",
        show_envvar=True,
        default="",
    )


def _project_name_option():
    return click.option(
        "-p",
        "--project",
        "project_name",
        help="Project name, used if it is not started with docker compose.",
        envvar="DB_BACKUP_PROJECT_NAME",
        show_envvar=True,
        default="",
    )


def _global_option():
    return click.option(
        "-g",
        "--global",
        "global_mode",
        help="Run in global mode, backup any container (e.g. not just the one defined in 'project'.).",
        envvar="DB_BACKUP_GLOBAL",
        show_envvar=True,
        is_flag=True,
        default=False,
    )


@cli.command()
@click.option(
    "-c",
    "--cron",
    "schedule",
    help="Cron schedule (https://crontab.guru), per default it runs at 2am every day.",
    envvar="DB_BACKUP_CRON",
    show_envvar=True,
    show_default=True,
    default="0 2 * * *",
)
@click.option(
    "-o",
    "--on-startup",
    is_flag=True,
    help="Run backup on startup as well.",
    envvar="ON_STARTUP",
    show_envvar=True,
    type=bool,
)
@_compression_option()
@_project_name_option()
@_backup_dir_option()
@_use_timestamp_option()
@_webhook_option()
@_global_option()
def backup_cron(schedule, on_startup, backup_dir, **kwargs):
    "Run backup based on the schedule."
    manager = BackupManager(backup_dir=Path(backup_dir), **kwargs)
    if on_startup:
        logger.info("Running backup on startup.")
        manager.backup(datetime.now())
    logger.info(f"Running backup with schedule '{schedule}'.")
    pycron.cron(schedule)(manager.backup)  # type: ignore
    pycron.start()


@cli.command()
@_compression_option()
@_project_name_option()
@_backup_dir_option()
@_use_timestamp_option()
@_webhook_option()
@_global_option()
def backup(backup_dir, **kwargs):
    "Run a manual backup."
    manager = BackupManager(
        backup_dir=Path(backup_dir),
        **kwargs,
    )
    sys.exit(manager.backup(datetime.now()))


@cli.command()
@_project_name_option()
@click.option(
    "-t",
    "--target",
    metavar="CONTAINER|SERVICE",
    help="Optional target which is either a container id, name or service name.",
    envvar="DB_TARGET",
)
@click.argument(
    "restore_file",  # type=click.Path(exists=True)
)  # TODO: support for directory and create filepath automatically
# warning on missing files
def restore(target, restore_file, **kwargs):
    "Restore a backup for a specific container."
    manager = BackupManager(**kwargs)
    manager.restore(target=target, restore_file=Path(restore_file))


if __name__ == "__main__":
    cli()
