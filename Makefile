
DISTRO?=alpine

PKG_VERSION=$(shell grep '^version =' pyproject.toml | sed -E "s/version = \"([^\"]+)\"/\1/")
TAG?=v$(PKG_VERSION)-$(DISTRO)
NEXT_TAG?=next-$(DISTRO)
REPO=db-backup-runner
DOCKER_IMAGE=${REPO}:${TAG}
DOCKER_IMAGE_SLIM=${REPO}:${TAG}-slim

ORGANIZATION=burgdev
REGISTRY=ghcr.io
NEXT_DOCKER_IMAGE=${REPO}:${NEXT_TAG}
NEXT_DOCKER_IMAGE_SLIM=${REPO}:${NEXT_TAG}-slim

.PHONY: init
init: ## Install the uv environment and install the pre-commit hooks
	@echo "Creating virtual environment using uv"
	@uv sync
	@ uv run invoke install
#@ uv run pre-commit install
#@echo "Run 'source .venv/bin/activate'"

#.PHONY: install
#install: ## Install the poetry environment and install the pre-commit hooks
#	@echo "🚀 Creating virtual environment using pyenv and poetry"
#	@uv sync
#	@ uv run pre-commit install
#	@echo "Run 'source .venv/bin/activate'"
#
#.PHONY: check
#check: ## Run code quality tools.
#	@echo "🚀 Checking uv lock file consistency with 'pyproject.toml': Running uv lock --locked"
#	@uv lock --locked
#	@echo "🚀 Linting code: Running pre-commit"
#	@uv run pre-commit run -a
#	@echo "🚀 Checking for obsolete dependencies: Running deptry"
#	@uv run deptry .
#	@echo "🚀 Static type checking: Running pyright"
#	@uv run pyright

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run pytest

.PHONY: build
build: clean-build ## Build wheel file using uv
	@echo "🚀 Creating wheel file"
	@uv build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@uv config pypi-token.pypi $(PYPI_TOKEN)
	@uv publish --dry-run
	@echo "🚀 Publishing."
	@uv publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve -a localhost:8083 -w src

#docker-login: # Login to ghcr (github container registry)
#	@echo "Make sure to have run:"
#	@echo "export GITHUB_USERNAME=user"
#	@echo "export GITHUB_TOKEN=token"
#	echo ${GITHUB_TOKEN} | docker login ghcr.io -u GITHUB_USERNAME --password-stdin

docker-push: docker-build docker-login # Push docker image
	docker push ${REGISTRY}/${ORGANIZATION}/${DOCKER_IMAGE}
	docker push ${REGISTRY}/${ORGANIZATION}/${NEXT_DOCKER_IMAGE}

.PHONY: docker_build
docker-build: ## Build docker image
	@echo "🚀 Docker image build: ${DOCKER_IMAGE}"
	DOCKER_BUILDKIT=1
	docker buildx build \
		--tag "$(DOCKER_IMAGE)" \
		--tag "$(NEXT_DOCKER_IMAGE)" \
		--tag "${REGISTRY}/${ORGANIZATION}/${DOCKER_IMAGE}" \
		--tag "${REGISTRY}/${ORGANIZATION}/${NEXT_DOCKER_IMAGE}" \
		.
	@echo "Build finished"

.PHONY: docker_slim
docker-slim: docker-build## Build slim docker image (based on docker build)
	bash -c 'mint slim --target $(DOCKER_IMAGE) \
		--tag "$(DOCKER_IMAGE_SLIM)" \
		--tag "$(NEXT_DOCKER_IMAGE_SLIM)" \
		--tag "${REGISTRY}/${ORGANIZATION}/${DOCKER_IMAGE_SLIM}" \
		--tag "${REGISTRY}/${ORGANIZATION}/${NEXT_DOCKER_IMAGE_SLIM}" \
		--network wodore-backend_postgresnet \
		--include-workdir  \
		--http-probe-off \
		--exec "db-backup-runner --help" \
		--mount "/var/run/docker.sock:/var/run/docker.sock:ro"'


.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := init
