from invoke.collection import Collection
from invoke.context import Context as Ctx
from invoke.tasks import task
from _logger import info, error, success, warning, echo, doc, header
from _env import env, EnvError
import check
import docker
import project


ns = Collection(project.install, project.release, project.update_venv, check, docker)


__all__ = (
    "install",
    "Ctx",
    "env",
    "EnvError",
    "info",
    "error",
    "success",
    "warning",
    "header",
    "echo",
    "doc",
)
