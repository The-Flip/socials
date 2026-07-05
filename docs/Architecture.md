# Architecture

`socials` is a Python 3.14 project managed with `uv`. It is young; this document describes
the current shape and the intended direction. Keep it current as modules land.

## Current

- **`socials/cli.py`** — the [Click](https://click.palletsprojects.com/) CLI entry point
  (`socials`). This is the first and, for now, only surface. Report commands hang off this
  group. User-facing failures raise `click.ClickException` (a clean message + non-zero exit),
  never a traceback.

## Intended direction

As features land (see [`plans/Product.md`](plans/Product.md) for the "why" and order), the
shape is expected to grow into roughly three layers, each introduced with its own
[`plans/`](plans/) ADR:

- **Reports** — the analyses that turn raw platform data into something worth reading. The
  core value; built and validated first, on the CLI.
- **Platform clients** — one per connected platform (Instagram first), behind a common
  interface so a report doesn't care which platform it's reading. The second integration is
  what proves the interface is reusable rather than Instagram-shaped.
- **Delivery** — where a report goes: the terminal now, a Discord channel next, a web
  interface later. Reports produce content; delivery targets consume it.

## Conventions

- **Secrets** (Instagram/Discord tokens) come from the environment — see `.env.example`.
  Never hardcode credentials.
- **Dependencies** are added with `uv add` / `uv add --dev` at their latest stable version.
- **One module, one responsibility.** Keep fetching, analysis, formatting, and delivery
  separable rather than fused into one command function.
