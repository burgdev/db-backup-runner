import click


from db_backup_runner.provider import BackupProviderBase


class PostgresBackupProvider(BackupProviderBase):
    name = "postgres"
    default_dump_binary = "pg_dump"
    # default_dump_binary = "pg_dumpall"
    default_dump_args = "-Fc"
    default_restore_binary = "pg_restore"
    default_restore_args = "-Fc -U USER -d DATABASE"
    plain_file_extension = ".dump"

    def dump(self) -> str:
        env = self.get_container_env()
        user = env.get("POSTGRES_USER", "postgres")

        return f"{self.get_dump_binary()} -U {user} {self.get_dump_args()}"

    def get_restore_args(self) -> str:
        env = self.get_container_env()
        user = env.get("POSTGRES_USER") or "postgres"
        # TODO get database from label or argument
        database = env.get("POSTGRES_DATABASE") or click.style(
            "DATABASE", fg="green", bold=True
        )
        return (
            (self.get_container_label("restore_args", self.default_restore_args) or "")
            .replace("USER", user)
            .replace("DATABASE", database)
        )

    # def restore(self, backup_file: Path) -> None:
    #    raise NotImplementedError(f"Restore is not supported yet for {self.name}.")
    # env = BackupBase.get_container_env(self.container)
    # user = env.get("POSTGRES_USER", "postgres")

    # restore_binary = BackupBase.get_label(self.container, "pgbackup-runner.restore_binary", "psql")
    # with backup_file.open("rb") as f:
    #    self.container.exec_run(
    #        f"bash -c '{restore_binary} -U {user}'", stdin=True
    #    )  # , socket_input=f) TODO: does not work
