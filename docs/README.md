# Development Guide

The development documentation for `socials`.

## Conventions & process

- **[Architecture.md](Architecture.md)** — system components and how they fit together
- **[Testing.md](Testing.md)** — test runner, layout, and conventions
- **[Workflow.md](Workflow.md)** — branch → AGY → PR → CodeRabbit → merge, and how conflicts are adjudicated

## The "why"

- **[plans/README.md](plans/README.md)** — the ADR convention: how we record the "why" of significant changes
- **[plans/Product.md](plans/Product.md)** — who the users are, the needs `socials` addresses, and the roadmap

## Agent instructions

`CLAUDE.md` and `AGENTS.md` (repo root) are **generated** from
[`AGENTS.src.md`](AGENTS.src.md). Edit the source and run `make agent-docs`; never edit the
generated files directly (a pre-commit hook enforces this).
