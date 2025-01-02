
![Image title](assets/favicon.png){ width=140, align=right }
# DB Backup Runner

**DB Backup Runner** is used to backup any database from other containers.
Since it uses the backup tool (e.g. `pgdump`) from inside the database container it is
easy to add support for many databases.

The script can also make backups from multiple containers and is configured with _labels_.

!!! note
    It works best together with `docker compose`, although it should work with docker alone,
    but at the moment it is only tested with `docker compose`. For more see [packages](packages.md/#pypi).

Each database which needs a backup need the `db-backup-runner.enable=true` label, as shown in the following
docker compose configuration file:


```yaml title="Example docker compose fil with two databases and a backup runner container"
services:
  db-backup:  # Backup container
    image: ghcr.io/burgdev/db-backup-runner:latest # (1)!
    restart: unless-stopped
    container_name: docker-db-auto-backup
    command: "backup-cron --on-startup" # optional (2)
    environment:
      DB_BACKUP_CRON: "0 4 * * *" # (3)!
      WEBHOOK: "https://my-webhook.io/myapp"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro" # required
      - ./backups:/tmp/db_backup_runner # required, backup directory

  app:
    image: myapp:latest
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/app_db
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

  postgis:
    image: postgis/postgis:16-3-alpine  # PostgreSQL with PostGIS support
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: app_db
    labels: # (4)!
      - "db-backup-runner.enable=true"
      # optional
      - `db-backup-runner.dump_args=-Ft`

  redis:
    image: redis:alpine
    labels:
      - "db-backup-runner.enable=true"
      # optional
      - "db-backup-runner.backup_provider=redis"
      - "db-backup-runner.webhook=none" # disable global webhook for this container
```

1. Backup [container](https://ghcr.io/burgdev/db-backup-runner) (~60MB), responsible to run a cron jobs which runs the backups
2. The `command` is only used if additional arguments are needed. The subcommand (in this case `backup-cron`) is required.
   It is also possible to use environment variables instead.
3. Schedule the backups, use cron [syntax](https://crontab.guru).
4. Labels are used to configure the backup for each container. Only the `db-backup-runner.enable=true` is required.

The backup container runs a cron job which backs up all container which are enabled and have a
backup provider.

At the moment the following providers are supported:

- Postgres (`db_dump`)

!!! warning
    Only postgres is tested at the moment, the others might not work yet!

- MariaDB (`mariadb-dump`)
- MySQL (`mysqldump`)
- Redis (`redis-cli`)

But it is easy to create additional providers and mount them into the backup container
(`./custom:/app/src/db_backup_runner/custom`), see [db_backup_runner.custom.provider][].
The custom backup providers are loaded first, this means you can overwrite existing providers (same name) or add new ones (different name).

## Command Arguments

This are the possible command arguments (or environment variables).

::: mkdocs-click
  :module: db_backup_runner.cli
  :command: backup_cron
  :prog_name: backup-cron
  :depth: 3
  :style: plain

The other `db-backup-runner` subcommands are documented [here](cli.md).

## Labels

Labels are used to control each containers backup.

#### Required

`db-backup-runner.enable = true|false`
:   Enabled or disable backup

#### Optional

`db-backup-runner.backup_provider = postres|mysql|mariadb|readis|...`
:   Provider, only needed if it cannot figure it out.

`db-backup-runner.dump_binary = <custom binary name or path>`
:   If the default command doesn't work.

`db-backup-runner.dump_args = <additional args>`
:   Additional arguments for the `dump` command.

`db-backup-runner.min_file_size = <number>`
:   A sanity check is done for the file size, this can be changed per container (default: 200)

`db-backup-runner.webhook = <custom webhook address>|none`
:   If one container should use a different webhook address or don't use it at all.

### Defaults

The default values are described in the API reference:

* [Postgres][db_backup_runner.provider.PostgresBackupProvider-attributes]

!!! warning
    Only postgres is tested at the moment, the others might not work yet!


* [MySQL][db_backup_runner.provider.MySQLBackupProvider-attributes]
* [MariaDB][db_backup_runner.provider.MariaDbBackupProvider-attributes]
* [Redis][db_backup_runner.provider.RedisBackupProvider-attributes]


## Restore

### Docker Compose

Restoring is not fully implemented yet, but you can create a bash script which
helps to restore the data base.
This gives you also the flexibility to change it accordingly to your needs.

```bash
 docker compose run db-backup restore ./backups/postgis/postgis.postgres.dump
 #> shows the backup commands
 # you can save it into a script
 docker compose run db-backup restore ./backups/postgis/postgis.postgres.dump restore.sh
 chmod +x restore.sh
 # make sure everything is correct, replace DATABASE with the correct database
 vim restore.sh
 ./restore.sh # run it from the host
```

Your can create the script for just one service:

```bash
 docker compose run db-backup restore --target redis ./.../redis.redis.rdb
```

This are the main commands needed to restore a database

```bash
# copy dump file into the docker container
docker compose cp backups/postgis/postgis.postgres.dump psql:/tmp/db.dump
docker compose exec postgis pg_restore -Fc -U USER -d DATABASE /tmp/db.dump
```

### Host

You can run the `db-backup-runner` [script directly](packages.md/#pypi) on your host.
Install this package and use the same commands as above without `docker compose run`
