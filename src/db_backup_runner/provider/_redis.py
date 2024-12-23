from pathlib import Path

from db_backup_runner.provider import BackupProviderBase


class RedisBackupProvider(BackupProviderBase):
    name = "redis"
    min_file_size: int = 50
    default_dump_binary = "redis-cli"
    plain_file_extension = ".rdb"

    def dump(self) -> str:
        return f"sh -c '{self.get_dump_binary()} {self.get_dump_args()} SAVE > /dev/null && cat /data/dump.rdb'"

    def restore(self, backup_file: Path) -> None:
        raise NotImplementedError(f"Restore is not supported yet for {self.name}.")
