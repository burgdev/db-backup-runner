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


@task(help={"force": "Force tag creation and pushing"})
def release(c: Ctx, force: bool = True):
    """Prepare a release, update CHANGELOG file and bump versions"""
    echo("🚀 Creating virtual environment using pyenv and poetry")
    out = c.run("rooster release")
    last_tag = None
    new_tag = None
    for line in out.stdout.split("\n"):
        if "last version tag" in line:
            last_tag = line.split(" ")[-1]
        elif "new version" in line:
            new_tag = line.split(" ")[-1]
    if new_tag:
        success(
            f"Bump from version '{last_tag}' to '{new_tag}'."
        ) if last_tag else success(f"Bump to version '{new_tag}'.")
        if input(f"Create new tag 'v{new_tag}' [N/y]: ").lower() in ["yes", "y"]:
            c.run(f"git tag -f 'v{new_tag}'")
            if input("Push tags [N/y]: ").lower() in ["yes", "y"]:
                c.run(f"git push origin 'v{new_tag}'")
    else:
        warning("Did not update to new version tag.")
