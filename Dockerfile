FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

LABEL org.opencontainers.image.name="DB Backup Runner"
LABEL org.opencontainers.image.authors="tobias@burgdev.ch"
LABEL org.opencontainers.image.source=https://github.com/burgdev/db-backup-runner
LABEL org.opencontainers.image.description="Run any db backups (and others) from inside its own docker container."


# hadolint ignore=DL3018
RUN apk update && \
  apk upgrade && \
  apk add --no-cache \
  git


ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --no-dev

COPY ./src ./pyproject.toml ./uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=README.md,target=README.md \
  uv sync --frozen --no-dev


FROM python:3.12-alpine

#ARG UID=1000 \
#  GID=1000
#
## hadolint ignore=DL3008
#RUN apk update \
#  && apk upgrade  \
#  # add user and group
#  && addgroup -g "${GID}"  app \
#  && adduser -h '/app' -G app -D -u "${UID}" --no-create-home app
#
#USER app

WORKDIR /app

# Copy the application from the builder
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["db-backup-runner"]
CMD ["backup-cron"]
