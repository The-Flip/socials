# Queued posts in the daily report

Status: Accepted (AGY-reviewed) — implementing on `feat/queued-posts`.

## Goal

Extend `socials report` so it shows not only **what already went out** (sent posts + engagement,
added in [buffer-24h-report.md](buffer-24h-report.md)) but also **what's coming up** — the Buffer
**queue**. The daily report becomes a full briefing: recent activity _and_ the upcoming/pending
pipeline.

## Background — the "why"

The Flip's social media is run by a loosely-organized group of volunteers ([Product.md](Product.md)).
Beyond "how did recent posts do," the team needs to know **whether the pipeline is healthy** — is
anything scheduled, or has the queue run dry? Surfacing the queue (and flagging an **empty** one) is
a small, high-value slice of that visibility, and a natural companion to the sent-activity report.

## Approach

Everything is available through the **existing Buffer integration** — no new credentials. Buffer's
`PostStatus` enum includes `scheduled` (the auto-publish queue) and `needs_approval` (awaiting
sign-off).

### Confirmed by probing (read-only, live)

- `posts(filter:{status: scheduled | needs_approval}, ...)` works; each node exposes `dueAt`
  (scheduled time), `status`, and `channel{ id service name }`.
- The account's **queue is currently empty** (0 scheduled / needs_approval / draft) — so live
  verification exercises the empty-state path; the populated path is covered by mocked tests.
- As with sent posts, **captions/`text` aren't exposed** by this token, and queued posts have no
  `externalLink` yet → the queue section keys on **time + channel**.

### Scope (confirmed with William)

- **Queued = `scheduled`** (listed with times) **+ `needs_approval`** (shown as an "awaiting
  approval" line). Drafts excluded — they have no send time and aren't really queued.
- **Show a count + everything scheduled in the next 7 days.** Awaiting-approval is shown as a count
  (approval isn't time-bound), listing time + channel where a `dueAt` exists.
- **An empty queue is an alert.** If nothing is scheduled in the window, the report says so
  prominently (`⚠ Nothing scheduled in the next 7 days.`) — actionable for the volunteers.

### Shape

- `socials/buffer.py` — new typed `QueuedPost` (`due_at`, channel, `status`, `media_type`) and
  `Queue` (`scheduled`, `awaiting_approval`, `truncated`); a
  `queued_posts(org_id, now, *, horizon_days=7)` reusing `_gql`, the `MAX_PAGES` cap, and
  `_parse_dt`. **Two separate queries** (Buffer's `status` filter is a single enum, and
  `needs_approval` isn't time-bound): a `dueAt`-windowed query for `scheduled`, and an unwindowed
  query for `needs_approval`. Scheduled posts are sorted by `due_at` ascending client-side. Each
  node also selects `assets { __typename }` so we can show a **media-type indicator** (`[Video]` /
  `[Photo]`) — otherwise the queue is a "blind" list of timestamps.
- `socials/report.py` — the queue is **decoupled from the activity `Report`** (keeps them
  composable for future standalone/Discord queue alerts): a pure `build_queue(queue, now, *,
horizon_days) -> QueueReport` and a separate `render_queue(queue_report)`, reusing `_service_label`
  / `_fmt_time` / `_display_tz` (times in `America/Chicago`, matching the sent section).
- `socials/cli.py` — `report` (with a new `--queue-days`, default `DEFAULT_QUEUE_HORIZON_DAYS = 7`)
  fetches sent posts (core) then the queue in a **graceful-degradation** block: if the queue fetch
  raises `BufferError`, still print the activity report and show `⚠ Could not fetch the queue` rather
  than failing the whole command. Prints `render_text(report)` then `render_queue(...)`.
- **State-aware alerts** in `render_queue`: nothing scheduled → `⚠ Nothing scheduled in the next 7
days` (+ "(but N awaiting approval)" when applicable); a running-low hint when the queue is nearly
  empty; a truncation note if `MAX_PAGES` was hit.
- Tests mock HTTP with **respx**, covering the populated queue, the empty/approval-aware alert,
  ordering, media-type labels, and graceful degradation on a queue-fetch error.

## Alternatives considered

- **Include drafts as "queued."** Rejected: drafts have no send time and aren't in the publish
  queue; counting them is noisy. `scheduled` + `needs_approval` is the meaningful pipeline.
- **Show the entire queue / only the next few.** Rejected in favour of a **7-day horizon** (William's
  call): scannable for a daily report while still covering the planning week.
- **A separate `socials queue` command.** Rejected: the ask is to enrich the _daily report_; one
  command that shows recent + upcoming is the intended briefing.
- **Server-side sort (`PostSortInput`).** Not relied upon — the sort-field enum introspected empty;
  sorting `scheduled` by `due_at` ascending client-side is simple and robust.

## Verification

- `make quality` + `make test` (respx-mocked, incl. the populated-queue path) green.
- Live (empty-state now): `uv run socials report` shows recent activity **and** the
  `⚠ Nothing scheduled…` line; the populated path is re-verifiable live once a post is scheduled.

## Review feedback incorporated

`make review-plan` (AGY) reviewed this ADR before implementation. Dispositions:

**Folded into the design (above):**

- **`needs_approval` vs `dueAt` window / single-enum filter** — use **two separate queries**
  (windowed `scheduled`, unwindowed `needs_approval`), so approval-backlog posts without a `dueAt`
  aren't silently dropped. (Confirmed by probing that a single-status filter works.)
- **Pagination truncation hazard** — the `dueAt` 7-day window already bounds the scheduled set well
  under the cap; still surface a **truncation warning** if `MAX_PAGES` is hit.
- **"Blind queue"** — select `assets { __typename }` and show a **media-type indicator**
  (`[Video]`/`[Photo]`) alongside time + channel.
- **Timezone** — render `due_at` in **America/Chicago** via `_display_tz`/`_fmt_time`.
- **State-aware alerts** — empty-queue alert is approval-aware; add a running-low hint.
- **Decoupling** — keep `Queue`/`queued_posts` and `build_queue`/`render_queue` **separate** from the
  activity `Report`, composed at the CLI, so a future standalone/Discord queue alert can reuse them.
- **Horizon config** — a `DEFAULT_QUEUE_HORIZON_DAYS` constant plus a `--queue-days` CLI option.
- **Error isolation** — a failed queue fetch **degrades gracefully** (activity report still prints).

**Confirmed, no change:** secrets handling (reuses `BufferClient`; `BufferError` never leaks the
token).
