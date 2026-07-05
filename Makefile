.PHONY: help test lint format typecheck quality precommit run agent-docs

help:
	@echo "socials Makefile commands:"
	@echo ""
	@echo "  make test       - Run the test suite (pytest)"
	@echo "  make lint       - Run ruff linter (auto-fix)"
	@echo "  make format     - Run ruff formatter"
	@echo "  make typecheck  - Run mypy type checking"
	@echo "  make quality    - Format, lint, and typecheck"
	@echo "  make precommit  - Run pre-commit hooks on all files"
	@echo "  make run        - Show the CLI help"
	@echo "  make agent-docs - Regenerate CLAUDE.md and AGENTS.md from docs/AGENTS.src.md"
	@echo ""

test:
	uv run pytest

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

typecheck:
	uv run mypy socials

quality: format lint typecheck
	@echo "All quality checks passed!"

precommit:
	uv run pre-commit run --all-files

run:
	uv run socials --help

agent-docs:
	uv run python scripts/build_agent_docs.py
