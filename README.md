# socials

`socials` is the social-media assistant for [The Flip](https://www.theflip.museum/), a
pinball museum whose social media is run by a group of volunteer contributors.

It gives that group **reporting, alerts, and other assistance** — starting with reports run
from the command line.

Some goals:

- Run reports on how The Flip's social accounts are doing
- Alert the team to things worth attention (gaps, spikes, opportunities)
- Deliver those reports automatically to a Discord channel
- Grow to a web interface over time
- Connect Instagram first, then more platforms

## Status

Early. The CLI scaffold runs; platform integrations are next. See
[`docs/plans/Product.md`](docs/plans/Product.md) for the "why" and the roadmap.

## Getting started

Requires **Python 3.14** and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                                            # install dependencies
uv run pre-commit install                          # commit hooks
uv run pre-commit install --hook-type pre-push     # pre-push test hook
uv run socials --help                              # see the CLI
```

## Development

See [`docs/README.md`](docs/README.md) for the development guide, conventions, and the
review workflow. Agent instructions live in `CLAUDE.md` / `AGENTS.md` (generated from
[`docs/AGENTS.src.md`](docs/AGENTS.src.md) — run `make agent-docs` after editing the source).
