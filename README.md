<h3 align="center"><b>DB Backup Runner</b></h3>
<p align="center">
  <a href="https://burgdev.github.io/db-backup-runner"><img src="https://burgdev.github.io/db-backup-runner/assets/favicon.png" alt="DB Backup Runner" width="80" /></a>
</p>
<p align="center">
    <em>Backup multiple database containers from one backup runner container.</em>
</p>
<p align="center">
    <b><a href="https://burgdev.github.io/db-backup-runner/">Documentation</a></b> | <b><a href="https://ghcr.io/burgdev/db-backup-runner">Packages</a></b>
</p>

---

**DB Backup Runner** is used to backup any database from other containers.
Since it uses the backup tool (e.g. `pgdump`) from inside the database container it is
easy to add support for many databases.

The script can also make backups from multiple containers and is configured with _labels_ (in docker compose).

**NOTE:** It works best together with `docker compose`, although it should work with docker alone,
          but at the moment it is only tested with `docker compose`.

For more information check out the [**documentation**](https://burgdev.github.io/db-backup-runner/).


### Credits

Inspired by

- <https://github.com/RealOrangeOne/docker-db-auto-backup> for some initial source code (2024/12)
- <https://github.com/prodrigestivill/docker-postgres-backup-local> for the idea with the docker labels
