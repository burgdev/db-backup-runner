![Image title](docs/assets/favicon.png)

### **[Documentation](burgdev.github.io/db-backup-runner/)** | [Packages](https://ghcr.io/burgdev/db-backup-runner)


# DB Backup Runner


**DB Backup Runner** is used to backup any database from other containers.
Since it uses the backup tool (e.g. `pgdump`) from inside the database container it is
easy to add support for many databases.

The script can also make backups from multiple containers and is configured with _labels_.

!!! note
    It works best together with `docker compose`, although it should work with docker alone,
    but at the moment it is only tested with `docker compose`.

Each database which needs a backup need the `db-backup-runner.enable=true` label, as shown in the following
docker compose configuration file:












Runs a container with a Python script which makes updates from other (database) containers.

The [container](https://ghcr.io/burgdev/db-backup-runner) needs the `db-backup-runner.enable` label to be set to `true` for the backup.

Here is a _docker-compose.yml_ file with two databases and one backup container.

```yaml
services:
  # Backup container
  db-backup:
    image: ghcr.io/burgdev/db-backup-runner:next-alpine # (~60MB)
    restart: unless-stopped
    container_name: docker-db-auto-backup
    command: "backup-cron --on-startup" # optional
    environment:
      DB_BACKUP_CRON: "0 4 * * *" # https://crontab.guru
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro" # required
      - ./backups:/tmp/db_backup_runner # backup directory

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
    labels:
      - "db-backup-runner.enable=true"
      # optional
      - `db-backup-runner.dump_args=-Ft`

  redis:
    image: redis:alpine
    labels:
      - "db-backup-runner.enable=true"
      # optional
      - "db-backup-runner.backup_provider=redis"
      - "db-backup-runner.webhook=none" # disable global webhook for thos container
```

The backup container runs a cron job which backs up all container which are enabled and have a
backup provider. At the moment the following providers are supported:

- Postgres (`db_dump`)
- MariaDB (`mariadb-dump`)
- MySQL (`mysqldump`)
- Redis (`redis-cli`)

But it is easy to create additional providers and mount them into the backup container
(`./custom:/app/src/db_backup_runner/custom`). The custom backup providers are loaded first, this means you can overwrite existing providers (same name) or add new ones (different name).

## Labels

- `db-backup-runner.enable=true|false`: Enabled or disable backup (**required**)

All other labels are optional and usually nor needed:

- `db-backup-runner.backup_provider=postres|mysql|mariadb|readis|...`: Provider, only needed if it cannot figure it out.
- `db-backup-runner.dump_binary=<custom binary name or path>`: If the default command doesn't work.
- `db-backup-runner.dump_args=<additional args>`: Additional arguments for the `dump` command.
- `db-backup-runner.min_file_size=<number>`: A sanity check is done for the file size, this can be changed per container (default: 200)
- `db-backup-runner.webhook=<custom webhook address>|none`: If one container should use a different webhook address or don't use it at all.

## Parameters or Environment Variables

- `-s`, `--cron`, `DB_BACKUP_CRON`: Cron schedule (<https://crontab.guru>), per default it runs at 2am every day.
- `-c`, `--compression`, `COMPRESSION`: Compression algorithm , supported values: plain, gzip, lzma, xz, bz2. Default is `plain`, it is better to use the compression by the DB if supported.
- `-w`, `--webhook`, `WEBHOOK`: Webhook address in case of success or error.
- `-t`, `--use-timestamp`, `USE_TIMESTAMP`: Add timestamp to filename.
- `-b`, `--backup-dir`, `BACKUP_DIR`: Different backup directory (only used if run outside of a container, defaults to `/tmp/db_backup_runner`).
- `-o`, `--on-startup`, `ON_STARTUP`: Run a backup when the container starts.

## Configuration

### Postgres

- `dump_binary`: `pg_dump`, change this to use e.g. `pg_dumpall`.
- `dump_args`: `-Fc -U USER`, remove it if `pg_dumpall` is used, which only supports `sql`.
- `restore_binary`: `pg_restore`
- `restore_args`: `-Fc -U USER -d DATABSE`

## Restore

### Docker Compose

Restoring is not fully implemented yet, but you can create a bash script which
helps to restore the data base.
This gives you also the flexibility to change it accordingly to your needs.

```bash
 docker compose exec db-backup db-backup-runner restore ./backups/postgis/postgis.postgres.dump
 #> shows the backup commands
 # you can save it into a script
 docker compose exec db-backup db-backup-runner restore ./backups/postgis/postgis.postgres.dump restore.sh
 chmod +x restore.sh
 # make sure everything is correct, replace DATABASE with the correct database
 vim restore.sh
 ./restore.sh # run it from the host
```

Your can create the script for just one service:

```bash
 docker compose exec db-backup db-backup-runner restore --target redis ./.../redis.redis.rdb
```

This are the main commands needed to restore a database

```bash
# copy dump file into the docker container
docker compose cp backups/postgis/postgis.postgres.dump psql:/tmp/db.dump
docker compose exec postgis pg_restore -Fc -U USER -d DATABASE /tmp/db.dump
```

### Host

You can run the `db-backup-runner` script directly on your host.
Install this package and use the same commands as above without `docker compose exec`

## Development

### Initial Setup

```bash
make
```

### Commands

After this the command `inv` is used:

```bash
inv --list
inv install        # install updates
inv check          # run all quality checks
inv docker.build   # build a docker image
```

For some scripts a `GITHUB_TOKEN` is required:

```bash
# for example with infisical
# source everthing
source <(infisical export --path /github)
# or only set  the token
export GITHUB_TOKEN=$(infisical secrets get --path /github GITHUB_TOKEN --plain)
```

### Release

For a release run `inv release`.
Merge this change into the `main` branch and tag it accordingly
and if needed create a GitHub release.

## Todos

- [x] Only upload images from the same stack
- [x] At the moment the `restore` function is not implemented yet -> generates bash script
- [ ] Upload files into the "cloud"

# Credits

Inspired by

- <https://github.com/RealOrangeOne/docker-db-auto-backup> for some initial source code (2024/12)
- <https://github.com/prodrigestivill/docker-postgres-backup-local> for the idea with the docker labels
