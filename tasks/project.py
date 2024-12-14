from tasks import info, error, success, warning, echo, env, task, Ctx, EnvError  # noqa: F401


@task
def update_venv(c: Ctx, dry: bool = False):
    """Updated venv activate script with custom commands"""
    commands = [
        "# custom command",
        'alias t="inv -p"',
        'alias tl="inv --list"',
        "source <(inv --print-completion-script bash)",
        "complete -F _complete_invoke -o default invoke inv t",
    ]
    for cmd in commands:
        info(f"Append '{cmd}' to activate script")
        c.run(f"echo '{cmd}' >> .venv/bin/activate") if not dry else None
    success("Updated venv activate script") if not dry else success(
        "Would have updated venv activate script"
    )
    info("Run 'source .venv/bin/activate'")


@task(help={"venv_update": "Updates venv activate script (runs per default)"})
def install(c: Ctx, venv_update: bool = True):
    """Install the uv environment and install the pre-commit hooks"""
    echo("🚀 Creating virtual environment using pyenv and poetry")
    c.run("uv sync")
    c.run("uv run pre-commit install")
    if venv_update:
        update_venv(c)
    success("Installation done, your are ready to go ...")
