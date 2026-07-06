"""Tests for building and rendering the 24h report (pure functions, no HTTP)."""

from datetime import UTC, datetime, timedelta

from socials.buffer import Channel, Metric, Post, Queue, QueuedPost, SentPosts
from socials.report import build_last_24h, build_queue, render_queue, render_text

NOW = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
IG = Channel("i", "theflipchicago", "instagram", False)
FB = Channel("f", "The Flip", "facebook", False)
YT = Channel("y", "TheFlipChicago", "youtube", False)


def post(hours_ago, channel, *, link="https://example/p", metrics=()):
    return Post(
        sent_at=NOW - timedelta(hours=hours_ago),
        channel_id=channel.id,
        channel_service=channel.service,
        channel_name=channel.name,
        external_link=link,
        metrics=tuple(Metric(*m) for m in metrics),
    )


def sent(posts, *, truncated=False):
    return SentPosts(posts=list(posts), truncated=truncated)


def test_windowing_excludes_posts_older_than_window():
    """A post 30h ago is excluded from a 24h report; a 1h-old post is included."""
    report = build_last_24h(sent([post(1, IG), post(30, IG)]), [IG], NOW)
    assert report.total_posts == 1


def test_channels_ordered_and_zero_post_channels_shown():
    """Preferred service order, and a connected channel with no posts still appears."""
    posts = [post(1, FB, metrics=[("Likes", 3, "count")]), post(2, IG)]
    report = build_last_24h(sent(posts), [IG, FB, YT], NOW)
    assert [c.service for c in report.channels] == ["instagram", "facebook", "youtube"]
    youtube = next(c for c in report.channels if c.service == "youtube")
    assert youtube.posts == []


def test_count_metrics_summed_percentage_excluded_from_totals():
    """Channel totals sum count-metrics; a percentage metric (Eng. Rate) is not summed."""
    posts = [
        post(1, FB, metrics=[("Impressions", 10, "count"), ("Eng. Rate", 5.0, "percentage")]),
        post(2, FB, metrics=[("Impressions", 5, "count"), ("Eng. Rate", 1.0, "percentage")]),
    ]
    report = build_last_24h(sent(posts), [FB], NOW)
    totals = {m.name: m.value for m in report.channels[0].totals}
    assert totals == {"Impressions": 15.0}


def test_render_instagram_shows_no_metrics_note_and_legend():
    report = build_last_24h(sent([post(1, IG, link="https://insta/1")]), [IG], NOW)
    out = render_text(report)
    assert "metrics not available via Buffer" in out
    assert "Instagram API in a future update" in out
    assert "https://insta/1" in out


def test_render_facebook_metrics_formatted():
    report = build_last_24h(sent([post(1, FB, metrics=[("Impressions", 63, "count")])]), [FB], NOW)
    assert "63 impressions" in render_text(report)


def test_empty_window_gives_friendly_message():
    out = render_text(build_last_24h(sent([]), [IG, FB], NOW))
    assert "No posts were published" in out
    assert "--hours 48" in out


def test_truncation_is_surfaced():
    report = build_last_24h(sent([post(1, IG)], truncated=True), [IG], NOW)
    assert "truncated" in render_text(report)


def qpost(days_ahead, service, *, name="acct", status="scheduled", media=None):
    return QueuedPost(
        due_at=NOW + timedelta(days=days_ahead),
        channel_id="x",
        channel_service=service,
        channel_name=name,
        status=status,
        media_type=media,
    )


def test_build_queue_filters_horizon_and_sorts():
    """Posts beyond the horizon are dropped; the rest are sorted soonest-first."""
    queue = Queue(
        scheduled=[qpost(5, "instagram"), qpost(1, "facebook"), qpost(30, "instagram")],
        awaiting_approval=[],
        truncated=False,
    )
    built = build_queue(queue, NOW, horizon_days=7)
    assert [p.channel_service for p in built.scheduled] == ["facebook", "instagram"]


def test_render_queue_empty_alert_is_approval_aware():
    queue = Queue(
        scheduled=[],
        awaiting_approval=[qpost(2, "instagram", status="needs_approval")],
        truncated=False,
    )
    out = render_queue(build_queue(queue, NOW))
    assert "Nothing scheduled" in out
    assert "awaiting approval" in out


def test_render_queue_lists_scheduled_with_media_and_low_warning():
    queue = Queue(
        scheduled=[qpost(1, "instagram", media="video")], awaiting_approval=[], truncated=False
    )
    out = render_queue(build_queue(queue, NOW))
    assert "Instagram" in out
    assert "[Video]" in out
    assert "running low" in out


def test_render_queue_truncation_note():
    queue = Queue(
        scheduled=[qpost(1, "facebook"), qpost(2, "facebook")], awaiting_approval=[], truncated=True
    )
    assert "truncated" in render_queue(build_queue(queue, NOW))
