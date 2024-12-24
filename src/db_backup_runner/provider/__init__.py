"""Backup provider classes"""

from db_backup_runner.provider._base import BackupProviderBase
from db_backup_runner.provider._mysql import MySQLBackupProvider
from db_backup_runner.provider._mariadb import MariaDbBackupProvider
from db_backup_runner.provider._postgres import PostgresBackupProvider
from db_backup_runner.provider._redis import RedisBackupProvider


__all__ = [
    "BackupProviderBase",
    "MariaDbBackupProvider",
    "MySQLBackupProvider",
    "PostgresBackupProvider",
    "RedisBackupProvider",
]

BACKUP_PROVIDERS = [
    MariaDbBackupProvider,
    MySQLBackupProvider,
    PostgresBackupProvider,
    RedisBackupProvider,
]
