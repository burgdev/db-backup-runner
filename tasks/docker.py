from tasks import info, error, success, warning, echo, env, task, Ctx, EnvError  # noqa: F401


@task
def login(c: Ctx, token: str | None = None):
    """Login to ghcr (github container registry)

    It uses the GITHUB_TOKEN environment variable to login."""
    try:
        token = token or env.str("GITHUB_TOKEN")
    except EnvError:
        token = input("Github package token: ")
    cmd = "docker login ghcr.io -u GITHUB_USERNAME -p $GITHUB_TOKEN"
    echo(cmd)
    try:
        c.run(cmd.replace("$GITHUB_TOKEN", token), pty=True, hide=True)
    except Exception:
        error("Login failed")
    success("Login successful")
