"""Test helpers for mocking Buffer's GraphQL API with respx.

All Buffer queries POST to the same URL, so the router dispatches by inspecting the query
string in each request body. Response shapes mirror what the live API actually returns
(captured during API probing).
"""

import json

import httpx

API_URL = "https://api.buffer.com"


def node(sent_at, service, name, link, metrics=(), *, channel_id="c"):
    """Build a post node as the API returns it. `metrics` is an iterable of (name, value, unit)."""
    return {
        "sentAt": sent_at,
        "channel": {"id": channel_id, "service": service, "name": name},
        "externalLink": link,
        "metrics": [{"name": n, "value": v, "unit": u} for n, v, u in metrics],
    }


def posts_page(nodes, *, has_next=False):
    return {
        "edges": [{"cursor": f"c{i}", "node": n} for i, n in enumerate(nodes)],
        "pageInfo": {"hasNextPage": has_next},
    }


def gql_router(*, account=None, channels=None, posts_pages=None, http_status=200, gql_error=None):
    """Return a respx side-effect that answers account/channels/posts queries in turn.

    `posts_pages` is a list of page payloads returned in order (for pagination tests).
    `http_status` != 200 makes every call fail with that status; `gql_error` returns a
    GraphQL error body on a 200.
    """
    pages = list(posts_pages or [])
    state = {"page": 0}

    def handler(request):
        if http_status != 200:
            return httpx.Response(http_status, json={"errors": [{"message": "http error"}]})
        if gql_error is not None:
            return httpx.Response(200, json={"errors": [{"message": gql_error}]})
        query = json.loads(request.content)["query"]
        if "organizations" in query:
            return httpx.Response(200, json={"data": {"account": account}})
        if "channels(" in query:
            return httpx.Response(200, json={"data": {"channels": channels or []}})
        if "posts(" in query:
            index = state["page"]
            state["page"] += 1
            page = pages[index] if index < len(pages) else posts_page([])
            return httpx.Response(200, json={"data": {"posts": page}})
        return httpx.Response(200, json={"data": {}})

    return handler
