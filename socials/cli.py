"""Command-line entry point for socials.

The CLI is the first surface (reports run from a terminal); Discord delivery and a web
interface come later. See docs/plans/Product.md for the "why".
"""

from datetime import UTC, datetime, timedelta

import click

from socials import config
from socials.buffer import BufferClient, BufferError
from socials.report import build_last_24h, render_text


@click.group()
@click.version_option()
def cli() -> None:
    """Reporting, alerts, and assistance for The Flip's social media volunteers."""
    config.load_env()


@cli.command()
@click.option("--hours", default=24, show_default=True, help="How far back to report.")
def report(hours: int) -> None:
    """Report what happened on The Flip's social channels in the last N hours.

    Reads from Buffer (all connected channels). Engagement metrics are shown where Buffer
    provides them; see docs/plans/buffer-24h-report.md.
    """
    if hours <= 0:
        raise click.BadParameter("must be a positive number of hours", param_hint="--hours")

    try:
        token = config.require_env("BUFFER_API_KEY")
    except config.MissingConfigError as exc:
        raise click.ClickException(str(exc)) from None

    click.echo("Fetching from Buffer…", err=True)
    now = datetime.now(UTC)
    start = now - timedelta(hours=hours)
    try:
        with BufferClient(token) as client:
            org_id = client.organization_id()
            channels = client.channels(org_id)
            sent = client.sent_posts(org_id, start, now)
    except BufferError as exc:
        raise click.ClickException(str(exc)) from None

    report_data = build_last_24h(sent, channels, now, hours=hours)
    click.echo(render_text(report_data), nl=False)
