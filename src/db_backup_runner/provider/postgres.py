from pathlib import Path


from db_backup_runner.provider import BackupProviderBase


class PostgresBackupProvider(BackupProviderBase):
    name = "postgres"
    default_dump_binary = "pg_dumpall"

    def dump(self) -> str:
        env = self.get_container_env()
        user = env.get("POSTGRES_USER", "postgres")

        return f"{self.get_dump_binary()} -U {user} {self.get_dump_args()}"

    def restore(self, backup_file: Path) -> None:
        raise NotImplementedError(f"Restore is not supported yet for {self.name}.")
        # env = BackupBase.get_container_env(self.container)
        # user = env.get("POSTGRES_USER", "postgres")

        # restore_binary = BackupBase.get_label(self.container, "pgbackup-runner.restore_binary", "psql")
        # with backup_file.open("rb") as f:
        #    self.container.exec_run(
        #        f"bash -c '{restore_binary} -U {user}'", stdin=True
        #    )  # , socket_input=f) TODO: does not work
