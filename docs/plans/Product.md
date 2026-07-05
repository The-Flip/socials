# Product: why socials exists

Status: Living document — the durable record of who the users are and what they need.

This is the "why" for the whole project. Feature ADRs in this folder link back here.
Update it when our understanding of the users or their needs changes.

## The users

The Flip is a pinball museum with a substantial community of **volunteers**. Its social media
is handled by a **loosely-organized group of contributors** — not a marketing department.
They are enthusiasts giving their time, with varying availability, tools, and technical
background. Coordination is informal (much of it happens in Discord).

`socials` is built for these contributors. Two things follow from that:

- **They are not engineers.** Output must be clear, errors must be actionable, and defaults
  must be sensible. A confusing traceback is a bug.
- **No one owns the full picture.** Because contribution is loose, no single person has a
  reliable view of how the accounts are doing or where the gaps are. Providing that shared
  view is the core value.

## The needs

What the loose structure makes hard, and what `socials` should make easy:

1. **Visibility** — a shared, trustworthy picture of how The Flip's social accounts are
   performing, without anyone having to log in and eyeball dashboards. This is why the first
   deliverable is **reporting**.
2. **Attention routing** — surfacing the things worth acting on (a post doing unusually well,
   a dormant account, a question that went unanswered) so volunteers can spend their limited
   time where it matters. This is why **alerts** are a first-class goal alongside reports.
3. **Low friction** — the team already lives in Discord, so reports and alerts should come to
   them there rather than requiring them to run a tool. This is why **Discord delivery**
   follows the CLI.
4. **Accessibility over time** — not every contributor will run a CLI. A **web interface**
   eventually lowers the barrier further.

## Roadmap and rationale

The order is deliberate — each stage delivers value and de-risks the next.

1. **CLI reports (now).** The fastest path to the core value (visibility) with the least
   machinery. A CLI lets us build and validate the reporting logic — fetching, analyzing,
   formatting — before committing to any delivery or hosting infrastructure.
2. **Discord delivery.** Once reports are trustworthy, push them to where the team already
   is. Removes the "someone has to remember to run it" friction and unlocks alerts.
3. **Web interface.** Broadens access beyond people comfortable with a terminal.

Platforms are added one at a time, behind a common interface:

- **Instagram first** — it's The Flip's primary/most active platform, so it delivers the most
  value soonest and is the best proving ground for the reporting and client abstractions.
- **More platforms over time** — the second integration is what validates that the platform
  abstraction is actually reusable rather than Instagram-shaped.

## Non-goals (for now)

- **Posting / scheduling content.** `socials` is about reporting, alerts, and assistance —
  read/observe, not publish. Revisit only with an explicit decision recorded here.
- **Replacing human judgment.** It routes attention; volunteers decide what to do.
