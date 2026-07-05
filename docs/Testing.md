# Testing

`socials` uses [pytest](https://docs.pytest.org/). Tests are a first-class part of every
change — the codebase aims for focused tests with good coverage.

## Running

```bash
make test          # run the suite
uv run pytest      # same thing
uv run pytest tests/test_cli.py            # a single file
uv run pytest tests/test_cli.py::test_help_lists_report_command   # a single test
```

The suite also runs automatically before `git push` (via the pre-push pre-commit hook) and in
CI on every PR.

## Conventions

- Tests live in `tests/`, **one file per module** (`socials/cli.py` → `tests/test_cli.py`).
- Each test has a **descriptive name and a docstring** saying what it verifies.
- Prefer exercising **real code paths** over mocks. If you must fake an external service
  (e.g. an Instagram HTTP call), do it deliberately and keep the seam small; don't mock away
  the behavior you're trying to test.
- Generate any secrets a test needs dynamically (`secrets.token_hex(16)`), never hardcode them.

## TDD

- **Bugs**: write a failing test that reproduces the bug first, then fix the code to make it
  pass.
- **New behavior**: include tests. Writing the test first is encouraged where it helps.
