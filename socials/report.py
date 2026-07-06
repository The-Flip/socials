"""Build and render the "last N hours" social activity report.

`build_last_24h` is pure — it turns Buffer data into a typed `Report` (no I/O, no formatting).
`render_text` turns a `Report` into the human-readable CLI output. Keeping them separate lets
future Discord (`render_markdown`) and web (`render_json`) formatters reuse the same builder.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from socials.buffer import Channel, Metric, Post, SentPosts

# The Flip is in Chicago; show times in its local timezone for the volunteers.
DISPLAY_TZ = "America/Chicago"
_PREFERRED_SERVICES = ("instagram", "facebook", "youtube")
_PREFERRED_METRICS = (
    "Impressions",
    "Reach",
    "Reactions",
    "Likes",
    "Comments",
    "Shares",
    "Clicks",
    "Eng. Rate",
)
_SERVICE_LABELS = {"instagram": "Instagram", "facebook": "Facebook", "youtube": "YouTube"}


@dataclass(frozen=True)
class ChannelReport:
    service: str
    name: str
    posts: list[Post]  # within the window, newest first
    totals: list[Metric]  # summed count-metrics across the channel's posts (empty if none)
    metrics_available: bool


@dataclass(frozen=True)
class Report:
    start: datetime
    end: datetime
    hours: int
    channels: list[ChannelReport]
    total_posts: int
    truncated: bool


def build_last_24h(
    sent: SentPosts, channels: list[Channel], now: datetime, *, hours: int = 24
) -> Report:
    """Turn fetched posts + channels into a structured report for the last `hours`.

    Filters posts to `sent_at` within [now - hours, now] (the server window is on `dueAt`;
    this makes it exact), groups them per channel, and sums count-metrics per channel.
    """
    start = now - timedelta(hours=hours)
    in_window = [p for p in sent.posts if start <= p.sent_at <= now]

    grouped: dict[str, list[Post]] = {}
    for post in in_window:
        grouped.setdefault(post.channel_id, []).append(post)

    channel_reports = []
    for channel_id, service, name in _ordered_channels(channels, in_window):
        posts = sorted(grouped.get(channel_id, []), key=lambda p: p.sent_at, reverse=True)
        channel_reports.append(
            ChannelReport(
                service=service,
                name=name,
                posts=posts,
                totals=_sum_count_metrics(posts),
                metrics_available=any(p.metrics for p in posts),
            )
        )

    return Report(
        start=start,
        end=now,
        hours=hours,
        channels=channel_reports,
        total_posts=len(in_window),
        truncated=sent.truncated,
    )


def render_text(report: Report, *, tz_name: str = DISPLAY_TZ) -> str:
    """Render a `Report` as the human-readable CLI report."""
    tz = _display_tz(tz_name)
    active = sum(1 for c in report.channels if c.posts)
    lines = [
        f"The Flip — social activity · last {report.hours}h",
        f"{_fmt_dt(report.start, tz)} – {_fmt_dt(report.end, tz)} · "
        f"{report.total_posts} post{_s(report.total_posts)} across "
        f"{active} channel{_s(active)}",
    ]
    if report.truncated:
        lines.append("(results truncated at the page limit — narrow the window with --hours)")
    lines.append("")

    if report.total_posts == 0:
        lines.append("No posts were published on any Buffer channel in this window.")
        lines.append("Try a wider window, e.g. --hours 48.")
        return "\n".join(lines).rstrip() + "\n"

    show_legend = False
    for channel in report.channels:
        count = len(channel.posts)
        header = f"{_service_label(channel.service)} ({channel.name}) — "
        header += f"{count} post{_s(count)}" if count else "no posts"
        lines.append(header)

        if channel.posts and not channel.metrics_available:
            lines.append("  metrics not available via Buffer *")
            show_legend = True
        elif channel.totals:
            lines.append(f"  {_fmt_metrics(channel.totals)}")

        for post in channel.posts:
            line = f"  • {_fmt_time(post.sent_at, tz)}"
            summary = _fmt_metrics(post.metrics)
            if summary:
                line += f"  {summary}"
            lines.append(line)
            if post.external_link:
                lines.append(f"      {post.external_link}")
        lines.append("")

    if show_legend:
        lines.append(
            "* Instagram Stories and some post types don't expose engagement metrics via Buffer;"
        )
        lines.append("  those will come from the Instagram API in a future update.")
    return "\n".join(lines).rstrip() + "\n"


def _ordered_channels(channels: list[Channel], posts: Iterable[Post]) -> list[tuple[str, str, str]]:
    """Return `(id, service, name)` for each channel to show, in display order.

    Connected channels come first (so zero-post channels still appear), in preferred-service
    order; any channel seen only in the posts (not in the channel list) is appended.
    """
    rows: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for channel in channels:
        if channel.is_disconnected or channel.id in seen:
            continue
        rows.append((channel.id, channel.service, channel.name))
        seen.add(channel.id)

    def rank(service: str) -> int:
        return (
            _PREFERRED_SERVICES.index(service)
            if service in _PREFERRED_SERVICES
            else len(_PREFERRED_SERVICES)
        )

    rows.sort(key=lambda r: (rank(r[1]), r[1], r[2]))

    for post in posts:
        if post.channel_id not in seen:
            rows.append((post.channel_id, post.channel_service, post.channel_name))
            seen.add(post.channel_id)
    return rows


def _sum_count_metrics(posts: list[Post]) -> list[Metric]:
    sums: dict[str, float] = {}
    for post in posts:
        for metric in post.metrics:
            if metric.unit == "count":
                sums[metric.name] = sums.get(metric.name, 0.0) + metric.value
    return [Metric(name=name, value=value, unit="count") for name, value in sums.items()]


def _fmt_metrics(metrics: Iterable[Metric]) -> str:
    ordered = sorted(metrics, key=_metric_rank)
    parts = []
    for metric in ordered:
        if metric.unit == "percentage":
            parts.append(f"{metric.value:g}% {metric.name.lower()}")
        else:
            parts.append(f"{int(round(metric.value))} {metric.name.lower()}")
    return " · ".join(parts)


def _metric_rank(metric: Metric) -> tuple[int, str]:
    rank = (
        _PREFERRED_METRICS.index(metric.name)
        if metric.name in _PREFERRED_METRICS
        else len(_PREFERRED_METRICS)
    )
    return (rank, metric.name)


def _service_label(service: str) -> str:
    return _SERVICE_LABELS.get(service, service.capitalize())


def _display_tz(name: str) -> ZoneInfo | timezone:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return UTC


def _fmt_dt(value: datetime, tz: ZoneInfo | timezone) -> str:
    return value.astimezone(tz).strftime("%b %d %I:%M %p %Z")


def _fmt_time(value: datetime, tz: ZoneInfo | timezone) -> str:
    return value.astimezone(tz).strftime("%b %d %I:%M %p")


def _s(count: int) -> str:
    return "" if count == 1 else "s"
