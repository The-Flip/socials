"""Tests for the Buffer GraphQL client — HTTP is mocked with respx against real response shapes."""

from datetime import UTC, datetime

import pytest
import respx
from buffer_api import API_URL, gql_router, node, posts_page

from socials.buffer import BufferClient, BufferError, Channel

WINDOW = (datetime(2026, 7, 4, tzinfo=UTC), datetime(2026, 7, 5, tzinfo=UTC))


def client() -> BufferClient:
    return BufferClient("test-token")


@respx.mock
def test_organization_id_returns_first_org() -> None:
    """organization_id() uses account.organizations (currentOrganization is forbidden)."""
    respx.post(API_URL).mock(
        side_effect=gql_router(account={"organizations": [{"id": "org1", "name": "Org"}]})
    )
    with client() as buffer:
        assert buffer.organization_id() == "org1"


@respx.mock
def test_organization_id_errors_when_no_org() -> None:
    """A token with no organization raises rather than returning None."""
    respx.post(API_URL).mock(side_effect=gql_router(account={"organizations": []}))
    with client() as buffer, pytest.raises(BufferError):
        buffer.organization_id()


@respx.mock
def test_channels_are_parsed() -> None:
    """Channels map to typed dataclasses, including the disconnected flag."""
    respx.post(API_URL).mock(
        side_effect=gql_router(
            channels=[
                {
                    "id": "i",
                    "name": "theflipchicago",
                    "service": "instagram",
                    "isDisconnected": False,
                },
                {"id": "f", "name": "FB", "service": "facebook", "isDisconnected": True},
            ]
        )
    )
    with client() as buffer:
        result = buffer.channels("org1")
    assert result == [
        Channel("i", "theflipchicago", "instagram", False),
        Channel("f", "FB", "facebook", True),
    ]


@respx.mock
def test_sent_posts_follows_pagination() -> None:
    """sent_posts walks pageInfo.hasNextPage and concatenates pages."""
    page1 = posts_page([node("2026-07-04T14:30:00.000Z", "instagram", "ig", "L1")], has_next=True)
    page2 = posts_page(
        [node("2026-07-04T13:30:00.000Z", "facebook", "fb", "L2", [("Likes", 3, "count")])],
        has_next=False,
    )
    respx.post(API_URL).mock(side_effect=gql_router(posts_pages=[page1, page2]))
    with client() as buffer:
        sent = buffer.sent_posts("org1", *WINDOW)
    assert [p.channel_service for p in sent.posts] == ["instagram", "facebook"]
    assert sent.posts[1].metrics[0] == sent.posts[1].metrics[0]  # metric parsed
    assert sent.truncated is False


@respx.mock
def test_sent_posts_truncates_at_page_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hitting MAX_PAGES stops pagination and flags truncation (no silent cap)."""
    monkeypatch.setattr("socials.buffer.MAX_PAGES", 2)
    page = posts_page([node("2026-07-04T14:30:00.000Z", "instagram", "ig", "L")], has_next=True)
    respx.post(API_URL).mock(side_effect=gql_router(posts_pages=[page, page, page]))
    with client() as buffer:
        sent = buffer.sent_posts("org1", *WINDOW)
    assert sent.truncated is True
    assert len(sent.posts) == 2


@respx.mock
def test_graphql_error_raises_buffer_error() -> None:
    """A GraphQL error in a 200 body becomes a BufferError."""
    respx.post(API_URL).mock(side_effect=gql_router(gql_error="bad query"))
    with client() as buffer, pytest.raises(BufferError, match="bad query"):
        buffer.organization_id()


@respx.mock
def test_http_401_gives_actionable_auth_message() -> None:
    """A 401 tells the user to check the key, and never leaks the token."""
    respx.post(API_URL).mock(side_effect=gql_router(http_status=401))
    with client() as buffer, pytest.raises(BufferError, match="rejected the API key") as exc:
        buffer.organization_id()
    assert "test-token" not in str(exc.value)


@respx.mock
def test_http_500_raises_buffer_error() -> None:
    respx.post(API_URL).mock(side_effect=gql_router(http_status=500))
    with client() as buffer, pytest.raises(BufferError, match="HTTP 500"):
        buffer.organization_id()
