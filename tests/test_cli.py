from click.testing import CliRunner
from db_backup_runner import cli
import pytest


@pytest.fixture
def runner():
    """Returns click cli runner or db-backup-runner."""

    def _runner(*args):
        runner = CliRunner()
        return runner.invoke(cli, args)

    return _runner


def test_cli_main(runner):
    """Test main help"""
    result = runner("--help")
    assert result.exit_code == 0
    assert "Usage: cli [OPTIONS] COMMAND [ARGS]..." in result.output


@pytest.mark.parametrize("subcmd", ["backup", "backup-cron", "restore"])
def test_cli_subcommands(runner, subcmd: str):
    """Test subcommand help"""
    result = runner(subcmd, "--help")
    assert result.exit_code == 0
    assert f"Usage: cli {subcmd}" in result.output
