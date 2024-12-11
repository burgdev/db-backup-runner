from pathlib import Path


from db_backup_runner.provider import BackupProviderBase


class MariaDbBackupProvider(BackupProviderBase):
    name = "mariadb"
    default_dump_args = "--all-databases"
    default_dump_binary = "mariadb-dump"

    def dump(self) -> str:
        env = self.get_container_env()

        if "MARIADB_ROOT_PASSWORD" in env:
            auth = "-p$MARIADB_ROOT_PASSWORD"
        elif "MYSQL_ROOT_PASSWORD" in env:
            auth = "-p$MYSQL_ROOT_PASSWORD"
        else:
            raise ValueError(
                f"Unable to find MySQL root password for {self.container.name}"
            )

        return f"bash -c '{self.get_dump_binary()} {auth} {self.get_dump_args()}'"

    def restore(self, backup_file: Path) -> None:
        raise NotImplementedError(f"Restore is not supported yet for {self.name}.")
