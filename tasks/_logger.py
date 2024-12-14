from rich import print as rprint
import sys
from environs import Env
import inspect

env = Env()
env.read_env()  # read .env file, if it exists


def echo(*args, **kwargs):
    rprint(*args, **kwargs)


def header(msg: str, symb="-", style="blue bold", max_length=80):
    length = len(msg)
    end = symb * (max_length - length) if length < max_length else symb * 2
    echo(f"[dim]{symb*2}[/] [{style}]{msg}[/] [dim]{end}[/]")


def info(msg: str):
    echo("[blue]Info   :[/]", msg)


def success(msg: str):
    echo("[green bold]Success:[/]", msg)


def warning(msg: str):
    echo("[yellow]Warning:[/]", msg)


def error(msg: str):
    echo(f"[red bold]Error:  [/] [red]{msg}[/]")
    sys.exit(1)


def doc():
    """Retrieve and print the docstring of the caller function."""
    caller_frame = inspect.stack()[1]
    caller = caller_frame.frame.f_globals.get(caller_frame.function)
    return inspect.getdoc(caller) or ""
