# Workflow

How changes get from idea to `main`. The two authoritative reviewers are **AGY** (William's
review agent, run interactively) and **CodeRabbit** (on the PR). Everything else is advisory.

## The loop

1. **Branch** — `type/short-description` (see the `branch` skill). Types: `feat`, `fix`,
   `docs`, `style`, `refactor`, `test`, `chore`.
2. **Plan → AGY** — for a non-trivial change, write the plan first and have **AGY** review it.
   Significant features also get a [`plans/*.md`](plans/README.md) ADR capturing the "why".
3. **Implement** with tests. Follow the patterns in [`Architecture.md`](Architecture.md) and
   [`Testing.md`](Testing.md).
4. **Local pre-PR review (advisory)** — run `/pre-pr-check`, which runs `make quality`, the
   tests, and the reviewer subagents (`documentation-reviewer`, `antipattern-scanner`,
   `clean-code-reviewer`, `code-smell-detector`). Address what matters.
5. **Change set → AGY** — have **AGY** review the finished change set **before opening the
   PR**. Fix any legitimate concerns first. **Do not open the PR until AGY has reviewed and
   those concerns are resolved.**
6. **PR → CodeRabbit** — only now open a PR against `main`. **CodeRabbit** reviews it
   automatically; address its findings in follow-up commits (`fix(...): address CodeRabbit review`).
7. **Merge** once CI is green.

The order is deliberate: **AGY first (pre-PR), then CodeRabbit (on the PR).** AGY sees a clean
change set, and CodeRabbit/CI only run once it's already in good shape.

## Quality gate

Before opening a PR:

```bash
make quality   # format + lint + typecheck
make test      # run the suite
```

Pre-commit hooks run formatting, linting, and typechecking on commit; the test suite runs on
push. CI re-runs the same gate on the PR.

## Reviewers and adjudication

- **AGY** and **CodeRabbit** are authoritative.
- The local reviewer subagents (and any other agent) are **advisory**: weigh their findings,
  don't blindly trust them, and don't blindly dismiss them either.
- When reviewers **conflict** and you can't reconcile them, **hand the conflict to William to
  adjudicate** — don't silently pick a side.

## Commits & PRs

Use [Conventional Commits](https://www.conventionalcommits.org/) for both commit messages and
PR titles (see the `commit` and `pr` skills). Keep the "why" in the body when it isn't obvious
from the summary.
