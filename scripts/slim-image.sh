#!/bin/sh

mint slim --http-probe-off --include-path /app  --exec "db-backup-runner backup" --mount "/var/run/docker.sock:/var/run/docker.sock:ro" db-backup-runner:dev --tag db-backup-runner:slim
