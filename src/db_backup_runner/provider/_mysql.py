from db_backup_runner.provider._mariadb import MariaDbBackupProvider


class MySQLBackupProvider(MariaDbBackupProvider):
    name = "mysql"
    default_dump_binary = "mysqldump"
