from tasks import (
    success,
    doc,
    header,
    task,
    Ctx,
)


@task
def uv_lock(c: Ctx):
    """Checking uv lock file consistency"""
    header(doc())
    c.run("uv lock --locked", echo=True)


@task
def lint(c: Ctx):
    """Linting code"""
    header(doc())
    c.run("uv run pre-commit run -a", echo=True)


@task
def fix(c: Ctx):
    """Fix code with ruff"""
    header(doc())
    c.run("uv run ruff check --fix .", echo=True)


@task
def deps(c: Ctx):
    """Checking for obsolete dependencies"""
    header(doc())
    c.run("uv run deptry .", echo=True)


@task
def types(c: Ctx):
    """Static type checking"""
    header(doc())
    c.run("uv run pyright  src", echo=True)


@task(pre=[uv_lock, lint, deps, types], default=True)
def check(c: Ctx):
    """Run code quality tools."""
    header("Summary")
    success("Code quality checks passed")
