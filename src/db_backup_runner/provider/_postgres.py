from db_backup_runner.provider import BackupProviderBase


class PostgresBackupProvider(BackupProviderBase):
    """Postgres backup provider"""

    name = "postgres"
    default_dump_binary = "pg_dump"
    # default_dump_binary = "pg_dumpall"
    default_dump_args = "-Fc -U USER DATABASE"
    default_restore_binary = "pg_restore"
    default_restore_args = "-Fc -U USER -d DATABASE"
    plain_file_extension = ".dump"

    def dump(self) -> str:
        """Overwrite dump method with custom postgres dump"""
        env = self.get_container_env()
        user = self.get_container_label("user", env.get("POSTGRES_USER") or "postgres")
        assert user is not None
        database_env = (
            env.get("POSTGRES_DATABASE", env.get("POSTGRES_DB")) or "postgres"
        )
        database = self.get_container_label("database", database_env)
        assert database is not None

        return f"{self.get_dump_binary()} {self.get_dump_args()}".replace(
            "USER", user
        ).replace("DATABASE", database)

    def get_restore_args(self) -> str:
        """Overwrite restore args with custom postgres arguments"""
        env = self.get_container_env()
        user = self.get_container_label("user", env.get("POSTGRES_USER") or "postgres")
        assert user is not None
        database_env = (
            env.get("POSTGRES_DATABASE", env.get("POSTGRES_DB")) or "postgres"
        )
        database = self.get_container_label("database", database_env)
        assert database is not None
        return (
            (self.get_container_label("restore_args", self.default_restore_args) or "")
            .replace("USER", user)
            .replace("DATABASE", database)
        )
