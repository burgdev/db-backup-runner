from invoke.collection import Collection
from invoke.context import Context as Ctx
from invoke.tasks import task
from _logger import info, error, success, warning, echo, doc, header
from _env import env, EnvError
import check
import docker
import project
import changelog
import test


@task
def help(c: Ctx):
    """Show this help"""
    c.run("inv --list", pty=True)


ns = Collection(
    project.install,
    project.release,
    project.version,
    project.update_venv,
    test.test,
    check,
    docker,
    changelog.changelog,
    help,
)


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
