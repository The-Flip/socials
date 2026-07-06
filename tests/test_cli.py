"""Tests for the CLI. Buffer HTTP is mocked with respx; `.env` loading is stubbed out."""

from datetime import UTC, datetime, timedelta

import pytest
import respx
from buffer_api import API_URL, gql_router, node, posts_page
from click.testing import CliRunner

from socials import config
from socials.cli import cli


def test_help_lists_report_command() -> None:
    """`socials --help` succeeds and advertises the report command."""
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "report" in result.output


def test_report_missing_key_errors_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without BUFFER_API_KEY the CLI fails with a helpful message, not a traceback."""
    monkeypatch.setattr(config, "load_env", lambda: None)
    monkeypatch.delenv("BUFFER_API_KEY", raising=False)
    result = CliRunner().invoke(cli, ["report"])
    assert result.exit_code != 0
    assert "BUFFER_API_KEY" in result.output


def test_report_rejects_nonpositive_hours(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_env", lambda: None)
    monkeypatch.setenv("BUFFER_API_KEY", "test-token")
    result = CliRunner().invoke(cli, ["report", "--hours", "0"])
    assert result.exit_code != 0


@respx.mock
def test_report_success_renders_channels(monkeypatch: pytest.MonkeyPatch) -> None:
    """The happy path renders Instagram (no metrics) and Facebook (metrics) sections."""
    monkeypatch.setattr(config, "load_env", lambda: None)
    monkeypatch.setenv("BUFFER_API_KEY", "test-token")
    recent = (datetime.now(UTC) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    respx.post(API_URL).mock(
        side_effect=gql_router(
            account={"organizations": [{"id": "org1", "name": "Org"}]},
            channels=[
                {
                    "id": "i",
                    "name": "theflipchicago",
                    "service": "instagram",
                    "isDisconnected": False,
                },
                {"id": "f", "name": "FB Page", "service": "facebook", "isDisconnected": False},
            ],
            posts_pages=[
                posts_page(
                    [
                        node(
                            recent, "instagram", "theflipchicago", "https://insta/1", channel_id="i"
                        ),
                        node(
                            recent,
                            "facebook",
                            "FB Page",
                            "https://fb/1",
                            [("Impressions", 63, "count"), ("Eng. Rate", 15.87, "percentage")],
                            channel_id="f",
                        ),
                    ]
                )
            ],
        )
    )
    result = CliRunner().invoke(cli, ["report"])
    assert result.exit_code == 0, result.output
    assert "Instagram (theflipchicago)" in result.output
    assert "metrics not available via Buffer" in result.output
    assert "63 impressions" in result.output
    assert "https://insta/1" in result.output
