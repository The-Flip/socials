# Buffer 24-hour report

Status: Accepted (AGY-reviewed) — implementing on `feat/buffer-24h-report`.

## Goal

The first real report: **what happened on The Flip's social accounts in the last 24 hours**, run
from the CLI (`socials report`). This is the first delivery of the _visibility_ the volunteer
social team needs (see [Product.md](Product.md)).

## Background — the users and the "why"

The Flip's social media is run by a loosely-organized group of volunteers; no one has a reliable
picture of how the accounts are doing (see [Product.md](Product.md)). A daily "here's what went out
and how it did" report is the smallest useful slice of that visibility, and it's the natural first
thing to build on the CLI before Discord delivery.

## Approach

### Source: Buffer, not the Instagram API (yet)

The Flip already publishes through **Buffer**, which aggregates all its channels. Sourcing from
Buffer's API means one integration covers Instagram, Facebook, and YouTube at once, and lets us
build and validate the reporting logic before taking on any single platform's API. A **read-only**
Buffer key is provided via `BUFFER_API_KEY` in `.env` (gitignored; a live secret — never commit or
print it).

### What the Buffer API gives us (confirmed by live probing)

- **Endpoint**: `POST https://api.buffer.com` (GraphQL), `Authorization: Bearer <key>`.
  (`graph.buffer.com` only answers introspection; real data must go to `api.buffer.com`.)
- **Org id**: `account.organizations[0].id`. `account.currentOrganization` is FORBIDDEN for this
  token, but `organizations` works — so we resolve the org from that list.
- **Channels**: `channels(input:{organizationId})` → instagram (`theflipchicago`), facebook, youtube.
- **Sent posts in a window**: `posts(input:{organizationId, filter:{status:sent,
dueAt:{start,end}}}, first, after)` with `pageInfo.hasNextPage` pagination. Each post gives
  `sentAt`, `channel{service,name}`, `externalLink` (permalink), and `metrics{name,value,unit}`.

### Known limitations (and how the report handles them)

- **Instagram post metrics come back empty** (the recent Instagram posts are Stories); only
  **Facebook** returns engagement metrics (Reactions, Impressions, Likes, Shares, Clicks, Comments,
  Eng. Rate). → The report **shows metrics where Buffer provides them and explicitly notes channels
  where it doesn't** ("metrics not available via Buffer"), rather than implying zero engagement.
- **Captions/`text` are empty** for every channel via this token. → The report references each post
  by **time + permalink (`externalLink`)** instead of caption text.
- **No `sentAt` filter server-side** (only `dueAt`/`createdAt` comparators). → We window server-side
  on `dueAt` (≈ send time for sent posts) and **refine client-side on `sentAt`** for an exact window.

### Scope decision (confirmed with William)

Report **all Buffer channels** in one 24h report — Instagram featured, Facebook metrics shown,
YouTube covered — not Instagram-only. Rationale: an Instagram-only report would be just links with no
performance data (metrics empty), whereas all-channels is genuinely useful today and still features
Instagram. Direct Instagram-API metrics are a later change set.

### Shape

- `socials/config.py` — load `.env` via `dotenv.find_dotenv()` (walks up from the cwd, so running
  from a subdirectory still works), fulfilling the deferred decision in
  [Architecture.md](../Architecture.md); `require_env("BUFFER_API_KEY")` with a clear,
  actionable error ("Set BUFFER_API_KEY — copy .env.example to .env"). Never log the value.
- `socials/buffer.py` — a sync **httpx** GraphQL client (`BufferClient`) with typed dataclasses
  (`Channel`, `Post`, `Metric`); GraphQL **variables**, not string interpolation. Robustness:
  - explicit `httpx` **timeout** (~10s) — never hang a volunteer;
  - a `BufferError` for failures that **carries the status and GraphQL message only — never the
    request headers/token** (a volunteer might paste a traceback into Discord);
  - check the top-level **`errors` key even on `200 OK`** (GraphQL returns errors in a 200 body);
  - map HTTP failures — including **`429` rate-limit** — to a friendly `BufferError`;
  - a **hard page cap** on pagination; if the window truncates at the cap, **say so in the output**
    (no silent caps).
- `socials/report.py` — a **pure** `build_last_24h(posts, channels, now)` returning a typed
  `Report` dataclass (structured data, not a string), plus a separate `render_text(report)`.
  Keeping build/render/IO separable lets future `render_markdown` (Discord) and `render_json` (web)
  reuse the same builder.
- `socials/cli.py` — the `report` command (`--hours`, default 24) wires it together; missing key or
  Buffer errors surface as `click.ClickException` (clean message, no traceback). Ergonomics for
  volunteers: a transient **"Fetching from Buffer…" line on stderr** (keeps stdout pipeable); a
  **friendly empty-window message** with a `--hours` hint; a **footer legend** explaining that
  Instagram Stories/some post types don't expose metrics via Buffer (coming from the Instagram API
  later).
- Tests mock HTTP with **respx** against the real response shapes.

## Alternatives considered

- **Start with the Instagram Graph API directly.** Rejected for now: more setup (app review, tokens,
  per-platform work) for a narrower result, and Buffer already aggregates the channels. Instagram-
  direct becomes worthwhile specifically to get the metrics Buffer doesn't expose — a later change set.
- **Instagram-only report via Buffer.** Rejected: Instagram metrics are empty via Buffer, so it would
  carry no performance data. All-channels is more useful now and still features Instagram.
- **Buffer classic REST API** (`api.bufferapp.com/1/`). Rejected: returns 401 "Public API tokens are
  not accepted for REST API access" — this token is for the GraphQL Public API.
- **Client-side-only windowing** (fetch all sent posts, filter in Python). Rejected as the primary
  path: server-side `dueAt` windowing is cheaper; we still refine on `sentAt` client-side for exactness.

## Verification

- `make quality` + `make test` (respx-mocked) green.
- Real end-to-end: `uv run socials report` prints the last-24h report against the live key;
  `--hours 72` widens the window; unsetting `BUFFER_API_KEY` yields a clean error.

## Review feedback incorporated

`make review-plan` (AGY) reviewed this ADR before implementation. Dispositions:

**Folded into the design (above):**

- **`.env` path trap** — `load_dotenv()` reads cwd only, breaking runs from another directory.
  → use `find_dotenv()` (upward search) + a clear missing-key error.
- **Secret exposure** — a raw traceback could leak the bearer token. → `BufferError` carries status
  - GraphQL message only, never request headers/token.
- **GraphQL errors in a `200`** — must check the `errors` key even on success. → already intended;
  now explicit.
- **Pagination runaway** — → hard page cap, and surface truncation in the output.
- **Rate limits / hangs** — → explicit `httpx` timeout; map `429`/HTTP errors to a friendly error.
- **Builder reuse for future deliveries** — → `build_last_24h` returns a typed `Report` dataclass;
  `render_text` is a separate formatter (Discord/web get their own later).
- **Empty window / liveness / metrics-gap** — → friendly empty message with a `--hours` hint, a
  stderr "Fetching…" line, and a footer legend about the Instagram metrics gap.

**Deferred (noted as future, not this change set):**

- **Global config (`~/.config/socials/`) and a `socials config set` helper** — genuinely useful once
  volunteers run the CLI directly, but they don't yet (delivery is via Discord, a later milestone);
  editing `.env` is fine for the developers building this now. `find_dotenv()` covers the near-term.
- **Escalating direct Instagram-API metrics** — remains the logical next change set; all-channels via
  Buffer (William's decision) meets the immediate visibility need.
