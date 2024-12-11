from db_backup_runner.provider import BackupProviderBase


class CustomProvider(BackupProviderBase):
    name = "custom"
    dump_binary = None
