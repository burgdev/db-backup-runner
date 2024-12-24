# Command Line Interface

A command line interface is used to backup and restore the databases.
For a one time backup the [`backup`](#db-backup-runner-backup) subcommand is used,
to run it as a cron job the [`backup-cron`](#db-backup-runner-backup-cron) subcommand is used.

```bash
db-backup-runner backup-cron
```

Usually the cron job is started as docker compose service,
which is the default entry point.
The documented arguments can be used either in `command` or `environment` section.

::: mkdocs-click
  :module: db_backup_runner.cli
  :command: cli
  :prog_name: db-backup-runner
  :depth: 1
  :style: plain
  :list_subcommands: True
