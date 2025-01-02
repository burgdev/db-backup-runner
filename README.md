<h3 align="center"><b>DB Backup Runner</b></h3>
<p align="center">
  <a href="https://burgdev.github.io/db-backup-runner"><img src="https://burgdev.github.io/db-backup-runner/assets/favicon.png" alt="DB Backup Runner" width="80" /></a>
</p>
<p align="center">
    <em>Backup multiple database containers from one backup runner container.</em>
</p>
<p align="center">
    <b><a href="https://burgdev.github.io/db-backup-runner/docu/">Documentation</a></b>
    | <b><a href="https://ghcr.io/burgdev/db-backup-runner">Docker</a></b>
    | <b><a href="https://pypi.org/project/db-backup-runner/">PyPi</a></b>
</p>

---

**DB Backup Runner** is used to backup any database from other containers.
Since it uses the backup tool (e.g. `pgdump`) from inside the database container it is
easy to add support for many databases.

The script can also make backups from multiple containers and is configured with _labels_ (in docker compose).

For more information check out the [**documentation**](https://burgdev.github.io/db-backup-runner/docu/).


### Credits

Inspired by

- <https://github.com/RealOrangeOne/docker-db-auto-backup> for some initial source code (2024/12)
- <https://github.com/prodrigestivill/docker-postgres-backup-local> for the idea with the docker labels
