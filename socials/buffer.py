"""Buffer GraphQL API client (read-only).

Talks to Buffer's Public GraphQL API at https://api.buffer.com — resolves the organization,
lists channels, and fetches sent posts in a time window. See docs/plans/buffer-24h-report.md
for the "why" and the API's quirks: metrics are empty for Instagram Stories, captions/`text`
aren't exposed, and posts filter on `dueAt` (not `sentAt`).

Errors surface as `BufferError` with a message that never includes the token or request headers.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx

API_URL = "https://api.buffer.com"
TIMEOUT_SECONDS = 10.0
PAGE_SIZE = 50
# Safety rail: cap pagination so an anomalous/huge window can't spin forever.
MAX_PAGES = 20


class BufferError(Exception):
    """A Buffer API call failed. Message is safe to show — never the token or request headers."""


@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    service: str
    is_disconnected: bool


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    unit: str | None


@dataclass(frozen=True)
class Post:
    sent_at: datetime
    channel_id: str
    channel_service: str
    channel_name: str
    external_link: str | None
    metrics: tuple[Metric, ...]


@dataclass(frozen=True)
class SentPosts:
    posts: list[Post]
    truncated: bool  # True if pagination hit MAX_PAGES before exhausting the window


@dataclass(frozen=True)
class QueuedPost:
    due_at: datetime | None  # scheduled time; may be absent for needs_approval posts
    channel_id: str
    channel_service: str
    channel_name: str
    status: str  # "scheduled" or "needs_approval"
    media_type: str | None  # "video" / "photo" / "media" / None (text-only)


@dataclass(frozen=True)
class Queue:
    scheduled: list[QueuedPost]  # in the requested window, sorted soonest-first
    awaiting_approval: list[QueuedPost]
    truncated: bool


_CHANNELS_QUERY = """
query ($org: OrganizationId!) {
  channels(input: { organizationId: $org }) { id name service isDisconnected }
}
"""

_POSTS_QUERY = """
query ($org: OrganizationId!, $start: DateTime!, $end: DateTime!, $first: Int!, $after: String) {
  posts(
    input: { organizationId: $org, filter: { status: sent, dueAt: { start: $start, end: $end } } }
    first: $first
    after: $after
  ) {
    edges { cursor node { sentAt channel { id service name } externalLink metrics { name value unit } } }
    pageInfo { hasNextPage }
  }
}
"""

# Queued posts (no metrics; `assets` lets us show a media-type indicator). `status` takes a single
# enum, and needs_approval posts aren't time-bound, so scheduled/approval are two separate queries.
_SCHEDULED_QUERY = """
query ($org: OrganizationId!, $start: DateTime!, $end: DateTime!, $first: Int!, $after: String) {
  posts(
    input: { organizationId: $org, filter: { status: scheduled, dueAt: { start: $start, end: $end } } }
    first: $first
    after: $after
  ) {
    edges { cursor node { dueAt status channel { id service name } assets { __typename } } }
    pageInfo { hasNextPage }
  }
}
"""

_APPROVAL_QUERY = """
query ($org: OrganizationId!, $first: Int!, $after: String) {
  posts(
    input: { organizationId: $org, filter: { status: needs_approval } }
    first: $first
    after: $after
  ) {
    edges { cursor node { dueAt status channel { id service name } assets { __typename } } }
    pageInfo { hasNextPage }
  }
}
"""


class BufferClient:
    """Read-only client for Buffer's Public GraphQL API."""

    def __init__(
        self, token: str, *, base_url: str = API_URL, client: httpx.Client | None = None
    ) -> None:
        self._token = token
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def __enter__(self) -> BufferClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        # Only close a client we created — a caller-supplied client is the caller's to manage.
        if self._owns_client:
            self._client.close()

    def _gql(self, query: str, variables: dict | None = None) -> dict:
        try:
            response = self._client.post(
                self._base_url,
                json={"query": query, "variables": variables or {}},
                headers={"Authorization": f"Bearer {self._token}"},
            )
        except httpx.RequestError as exc:
            # `from None`: don't chain the original — its .request carries the auth header.
            raise BufferError(f"Could not reach Buffer ({type(exc).__name__}).") from None

        if response.status_code in (401, 403):
            raise BufferError(
                f"Buffer rejected the API key (HTTP {response.status_code}). "
                "Check that BUFFER_API_KEY is set to a current, valid token."
            )
        if response.status_code == 429:
            raise BufferError("Buffer API rate limit exceeded. Please try again in a few minutes.")
        if response.status_code >= 400:
            raise BufferError(f"Buffer API returned HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError:
            raise BufferError("Buffer API returned a non-JSON response.") from None

        # GraphQL reports errors inside a 200 OK body — check even on success.
        errors = payload.get("errors")
        if errors:
            first = errors[0]
            message = first.get("message") if isinstance(first, dict) else str(first)
            raise BufferError(f"Buffer API error: {message or 'unknown error'}")
        return payload.get("data") or {}

    def organization_id(self) -> str:
        """Resolve the organization id (first of `account.organizations`).

        `account.currentOrganization` is forbidden for this token, so we use `organizations`.
        """
        data = self._gql("query { account { organizations { id name } } }")
        orgs = (data.get("account") or {}).get("organizations") or []
        if not orgs:
            raise BufferError("No Buffer organization is available for this token.")
        return orgs[0]["id"]

    def channels(self, org_id: str) -> list[Channel]:
        data = self._gql(_CHANNELS_QUERY, {"org": org_id})
        return [
            Channel(
                id=c["id"],
                name=c.get("name") or "",
                service=c.get("service") or "unknown",
                is_disconnected=bool(c.get("isDisconnected")),
            )
            for c in (data.get("channels") or [])
        ]

    def _collect[T](
        self, query: str, base_vars: dict, parse: Callable[[dict], T]
    ) -> tuple[list[T], bool]:
        """Page through a `posts(...)` query, returning (items, truncated_at_cap)."""
        items: list[T] = []
        after: str | None = None
        for _ in range(MAX_PAGES):
            data = self._gql(query, {**base_vars, "first": PAGE_SIZE, "after": after})
            conn = data.get("posts") or {}
            edges = conn.get("edges") or []
            items.extend(parse(e["node"]) for e in edges)
            if not (conn.get("pageInfo") or {}).get("hasNextPage") or not edges:
                return items, False
            after = edges[-1].get("cursor")
        return items, True

    def sent_posts(self, org_id: str, start: datetime, end: datetime) -> SentPosts:
        """Fetch posts with status `sent` whose `dueAt` falls in [start, end], paginated."""
        posts, truncated = self._collect(
            _POSTS_QUERY,
            {"org": org_id, "start": _to_iso(start), "end": _to_iso(end)},
            _parse_post,
        )
        return SentPosts(posts=posts, truncated=truncated)

    def queued_posts(self, org_id: str, now: datetime, *, horizon_days: int = 7) -> Queue:
        """Fetch the queue: `scheduled` posts due within the horizon, plus `needs_approval`.

        Two queries because Buffer's `status` filter is a single enum and needs_approval posts
        aren't time-bound. Scheduled posts are sorted soonest-first.
        """
        scheduled, sched_truncated = self._collect(
            _SCHEDULED_QUERY,
            {
                "org": org_id,
                "start": _to_iso(now),
                "end": _to_iso(now + timedelta(days=horizon_days)),
            },
            _parse_queued,
        )
        approval, appr_truncated = self._collect(_APPROVAL_QUERY, {"org": org_id}, _parse_queued)
        scheduled.sort(key=lambda q: q.due_at or _FAR_FUTURE)
        return Queue(
            scheduled=scheduled,
            awaiting_approval=approval,
            truncated=sched_truncated or appr_truncated,
        )


_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)  # sorts due_at=None queued posts last


def _to_iso(value: datetime) -> str:
    """Format a datetime as UTC ISO-8601 with a trailing Z (the form Buffer accepts)."""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_dt(value: str) -> datetime:
    # Python 3.11+ fromisoformat parses the trailing "Z" natively.
    return datetime.fromisoformat(value)


def _parse_post(node: dict) -> Post:
    channel = node.get("channel") or {}
    metrics = tuple(
        Metric(name=m["name"], value=float(m["value"]), unit=m.get("unit"))
        for m in (node.get("metrics") or [])
        if m.get("value") is not None
    )
    return Post(
        sent_at=_parse_dt(node["sentAt"]),
        channel_id=channel.get("id") or "",
        channel_service=channel.get("service") or "unknown",
        channel_name=channel.get("name") or "",
        external_link=node.get("externalLink"),
        metrics=metrics,
    )


def _parse_queued(node: dict) -> QueuedPost:
    channel = node.get("channel") or {}
    due = node.get("dueAt")
    return QueuedPost(
        due_at=_parse_dt(due) if due else None,
        channel_id=channel.get("id") or "",
        channel_service=channel.get("service") or "unknown",
        channel_name=channel.get("name") or "",
        status=node.get("status") or "",
        media_type=_media_type(node.get("assets") or []),
    )


def _media_type(assets: list[dict]) -> str | None:
    """Derive a display label from asset __typenames (e.g. VideoAsset → 'video')."""
    kinds = {a["__typename"].removesuffix("Asset").lower() for a in assets if a.get("__typename")}
    kinds.discard("")
    if not kinds:
        return None
    if len(kinds) == 1:
        return next(iter(kinds))
    return "media"
