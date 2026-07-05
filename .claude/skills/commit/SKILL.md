---
name: commit
description: Generates commit messages and creates commits. Use when writing commit messages, committing changes, or reviewing staged changes.
---

# Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format.

## Format

```text
<type>(<scope>): <description>

[optional body]
```

## Types

- `feat`: User-facing features or behavior changes (must change production code)
- `fix`: Bug fixes (must change production code)
- `docs`: Documentation only
- `style`: Code style/formatting (no logic changes)
- `refactor`: Code restructuring without behavior change
- `test`: Adding or updating tests
- `chore`: CI/CD, tooling, dependency bumps, configs (no production code)

## Scopes

Optional. Use when it adds clarity. Examples: `cli`, `report`, `instagram`, `discord`,
`config`.

## Examples

```text
feat(instagram): add engagement report
fix(instagram): refresh access token before expiry
refactor(report): extract platform client interface
chore: add ruff linting configuration
docs: capture reporting user needs in Product ADR
test(cli): cover the report placeholder command
```

## Instructions

1. Run `git diff --staged` to see staged changes
2. Analyze the changes and determine the appropriate type
3. Write a concise description (under 72 characters)
4. Add body only if the "why" isn't obvious from the description
