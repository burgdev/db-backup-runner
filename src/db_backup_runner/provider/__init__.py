from db_backup_runner.provider.base import BackupProviderBase
from db_backup_runner.provider.mysql import MySQLBackupProvider
from db_backup_runner.provider.mariadb import MariaDbBackupProvider
from db_backup_runner.provider.postgres import PostgresBackupProvider
from db_backup_runner.provider.redis import RedisBackupProvider


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
