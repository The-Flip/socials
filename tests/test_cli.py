"""Tests for the CLI entry point.

These assert the CLI is wired up and that the placeholder `report` command fails
cleanly (a non-zero exit with a helpful message) rather than crashing — so the
scaffold behaves well before any real report exists.
"""

from click.testing import CliRunner

from socials.cli import cli


def test_help_lists_report_command() -> None:
    """`socials --help` succeeds and advertises the report command."""
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "report" in result.output


def test_report_exits_cleanly_when_unimplemented() -> None:
    """`socials report` fails with a non-zero code and a helpful message, not a traceback."""
    result = CliRunner().invoke(cli, ["report"])
    assert result.exit_code != 0
    assert result.exception is None or isinstance(result.exception, SystemExit)
    assert "implemented" in result.output.lower()
    assert "instagram" in result.output.lower()
