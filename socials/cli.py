"""Command-line entry point for socials.

The CLI is the first surface (reports run from a terminal); Discord delivery and a web
interface come later. See docs/plans/Product.md for the "why".
"""

from datetime import UTC, datetime, timedelta

import click

from socials import config
from socials.buffer import BufferClient, BufferError, Queue
from socials.report import (
    DEFAULT_QUEUE_HORIZON_DAYS,
    build_last_24h,
    build_queue,
    render_queue,
    render_text,
)


@click.group()
@click.version_option()
def cli() -> None:
    """Reporting, alerts, and assistance for The Flip's social media volunteers."""
    config.load_env()


# Posts are windowed server-side on `dueAt` (scheduled time) but reported on `sentAt` (actual
# send time). Fetch a little earlier so a post that sent slightly after its scheduled time
# isn't missed; build_last_24h then filters exactly on `sentAt`.
_FETCH_SKEW = timedelta(hours=6)


@cli.command()
@click.option(
    "--hours",
    default=24,
    show_default=True,
    type=click.IntRange(min=1),
    help="How far back to report.",
)
@click.option(
    "--queue-days",
    default=DEFAULT_QUEUE_HORIZON_DAYS,
    show_default=True,
    type=click.IntRange(min=1),
    help="How far ahead to show the queue.",
)
def report(hours: int, queue_days: int) -> None:
    """Report recent activity and the upcoming queue for The Flip's social channels.

    Reads from Buffer (all connected channels). Engagement metrics are shown where Buffer
    provides them; see docs/plans/buffer-24h-report.md and queued-posts-report.md.
    """
    try:
        token = config.require_env("BUFFER_API_KEY")
    except config.MissingConfigError as exc:
        raise click.ClickException(str(exc)) from None

    click.echo("Fetching from Buffer…", err=True)
    now = datetime.now(UTC)
    start = now - timedelta(hours=hours)
    queue: Queue | None = None
    try:
        with BufferClient(token) as client:
            org_id = client.organization_id()
            channels = client.channels(org_id)
            sent = client.sent_posts(org_id, start - _FETCH_SKEW, now)
            # The queue is secondary — if it fails, still show the activity report.
            try:
                queue = client.queued_posts(org_id, now, horizon_days=queue_days)
            except BufferError:
                queue = None
    except BufferError as exc:
        raise click.ClickException(str(exc)) from None

    click.echo(render_text(build_last_24h(sent, channels, now, hours=hours)), nl=False)
    click.echo("")
    if queue is None:
        click.echo("Queued — could not fetch the queue from Buffer this time.")
    else:
        click.echo(render_queue(build_queue(queue, now, horizon_days=queue_days)), nl=False)
