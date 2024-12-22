from tasks import info, error, success, warning, echo, env, task, header, Ctx, EnvError  # noqa: F401


@task(default=True)
def entry(c: Ctx, latest: bool = False):
    scope = "--latest" if latest else "--current"
    entry = c.run(
        f"git-cliff {scope} --strip all | tail -n +2", hide=True
    ).stdout.strip()
    echo(entry)
