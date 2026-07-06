"""Test helpers for mocking Buffer's GraphQL API with respx.

All Buffer queries POST to the same URL, so the router dispatches by inspecting the query
string in each request body. Response shapes mirror what the live API actually returns
(captured during API probing).
"""

import json

import httpx

API_URL = "https://api.buffer.com"


def node(sent_at, service, name, link, metrics=(), *, channel_id="c"):
    """Build a sent-post node as the API returns it. `metrics` is (name, value, unit) tuples."""
    return {
        "sentAt": sent_at,
        "channel": {"id": channel_id, "service": service, "name": name},
        "externalLink": link,
        "metrics": [{"name": n, "value": v, "unit": u} for n, v, u in metrics],
    }


def queued_node(due_at, service, name, *, status="scheduled", channel_id="c", assets=()):
    """Build a queued-post node. `assets` is a list of __typename strings (e.g. 'VideoAsset')."""
    return {
        "dueAt": due_at,
        "status": status,
        "channel": {"id": channel_id, "service": service, "name": name},
        "assets": [{"__typename": a} for a in assets],
    }


def posts_page(nodes, *, has_next=False):
    return {
        "edges": [{"cursor": f"c{i}", "node": n} for i, n in enumerate(nodes)],
        "pageInfo": {"hasNextPage": has_next},
    }


def gql_router(
    *,
    account=None,
    channels=None,
    posts_pages=None,
    scheduled_pages=None,
    approval_pages=None,
    http_status=200,
    gql_error=None,
):
    """Return a respx side-effect answering account/channels/sent/scheduled/approval queries.

    The `*_pages` lists are returned in order (for pagination tests). `http_status` != 200 makes
    every call fail with that status; `gql_error` returns a GraphQL error body on a 200.
    """
    pages = {
        "sent": list(posts_pages or []),
        "scheduled": list(scheduled_pages or []),
        "approval": list(approval_pages or []),
    }
    counters = {"sent": 0, "scheduled": 0, "approval": 0}

    def pick(key):
        index = counters[key]
        counters[key] += 1
        return pages[key][index] if index < len(pages[key]) else posts_page([])

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
            if "status: scheduled" in query:
                key = "scheduled"
            elif "status: needs_approval" in query:
                key = "approval"
            else:
                key = "sent"
            return httpx.Response(200, json={"data": {"posts": pick(key)}})
        return httpx.Response(200, json={"data": {}})

    return handler
