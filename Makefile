.PHONY: help test lint format typecheck quality precommit run agent-docs review-plan review-change

help:
	@echo "socials Makefile commands:"
	@echo ""
	@echo "  make test         - Run the test suite (pytest)"
	@echo "  make lint         - Run ruff linter (auto-fix)"
	@echo "  make format       - Run ruff formatter"
	@echo "  make typecheck    - Run mypy type checking"
	@echo "  make quality      - Format, lint, and typecheck"
	@echo "  make precommit    - Run pre-commit hooks on all files"
	@echo "  make run          - Show the CLI help"
	@echo "  make agent-docs   - Regenerate CLAUDE.md and AGENTS.md from docs/AGENTS.src.md"
	@echo "  make review-plan  - Review a plan doc with the agy (AGY) CLI. e.g. PLAN=docs/plans/x.md"
	@echo "  make review-change- Review the current branch's change set with the agy (AGY) CLI"
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

# AGY (Google Antigravity's `agy` CLI) reviews in read-only print mode; it critiques, it does
# not edit files. AGY reviews the plan before implementation, and the change set before the PR.
review-plan:
ifndef PLAN
	$(error Usage: make review-plan PLAN=docs/plans/<name>.md)
endif
	agy --add-dir "$(dir $(abspath $(PLAN)))" -p "You are a distinguished software engineer doing a critical design review. Read $(abspath $(PLAN)) and critique it for soundness, gaps, and risks — especially maintainability, secrets handling, third-party API-integration robustness, and CLI ergonomics for non-engineer volunteers. Do NOT modify any files; provide a written critique only."

review-change:
	agy --add-dir "$(CURDIR)" -p "You are a distinguished software engineer doing a critical pre-PR code review of a finished change set. Review the changes on the current git branch relative to main — run 'git -C $(CURDIR) diff main...HEAD' and 'git -C $(CURDIR) log main..HEAD' to see them. Critique for correctness, maintainability, security (especially secrets handling), and CLI ergonomics for non-engineer volunteers. Do NOT modify any files; provide a written critique only, as a numbered list of findings with severity (blocker/major/minor/nit) and a concrete suggestion each."
