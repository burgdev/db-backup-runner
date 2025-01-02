## :simple-docker: Docker

[Docker images](https://github.com/burgdev/db-backup-runner/pkgs/container/db-backup-runner) are created with the following tags:

- `latest`: latest stable version
- `major`, `major.minor` and `major.minor.rev` tags
- `edge`: unstable development version


=== "Docker Compose"
    It is recommaded to use `docker compose`:

    ```yaml title="Example docker compose fil with two databases and a backup runner container"
    services:
      db-backup:
        image: ghcr.io/burgdev/db-backup-runner:next-alpine
        restart: unless-stopped
        container_name: docker-db-auto-backup
        volumes:
          - "/var/run/docker.sock:/var/run/docker.sock:ro" # required
          - ./backups:/tmp/db_backup_runner # required, backup directory
    ```
    Run a custom command:

    ```bash
    $ docker compose up # start services
    $ docker compose run db-backup [OPTIONS] COMMAND [ARGS]... # (1)!
    ```

    1. Run `db-backup-runner` subcommands.

=== "Docker"
    It is also possible to run it with docker directly:

    ```bash title="Pull latest docker image"
    $ docker pull ghcr.io/burgdev/db-backup-runner:latest
    $ docker run --rm -it \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v ./backups:/tmp/db_backup_runner ghcr.io/burgdev/db-backup-runner:latest \
        backup --project my-project
    ```
    !!! tip
        A `--project` name is needed or the `--global` flag in order to find the backup containers.

## :simple-pypi: PyPi


The script is also published as [PyPi package](https://pypi.org/project/db-backup-runner/).

=== "`uv`"

    Run it as [`uv`](https://docs.astral.sh/uv/) tool:

    ```bash
    $ uvx db-backup-runner [OPTIONS] COMMAND [ARGS]...
    ```

=== "`pipx`"

    Install it in isolated environment with `pipx`:

    ```bash
    $ pipx install db-backup-runner
    $ db-backup-runner [OPTIONS] COMMAND [ARGS]...
    ```

=== "`pip`"

    Install it with `pip`:

    ```bash
    $ pip install db-backup-runner
    $ db-backup-runner [OPTIONS] COMMAND [ARGS]...
    ```
