---
description: Run the pre-PR quality checklist for socials
---

<!-- Adapted from https://github.com/matsengrp/plugins (MIT License) -->

# Pre-PR Quality Checklist

You are helping the user prepare code for a pull request by guiding them through a quality checklist.

These local reviews are **advisory** — evaluate their findings carefully, but the
authoritative reviewers are **AGY** (the finished change set) and **CodeRabbit** (on the PR).
When reviewers conflict and you can't reconcile them, hand the conflict to William to
adjudicate. See [`docs/Workflow.md`](../../docs/Workflow.md).

## Your Role

Guide the user through each step systematically. For each step:

1. Explain what needs to be done
2. Execute the required checks/commands
3. Report the results clearly
4. Only proceed to the next step after the current step passes or the user acknowledges issues

## Checklist Steps

### 1. Issue Compliance Verification (if applicable)

- Ask the user for the GitHub issue number they're working on (if any)
- Use `gh issue view <number>` to fetch the issue details
- Review ALL requirements and verify completion
- If a requirement cannot be met, STOP and discuss with the user before proceeding

### 2. Code Quality Foundation

- Run `make quality` (format + lint + typecheck)
- Report any files modified or errors found
- If errors, STOP and require fixes before proceeding

### 3. Advisory Reviews

**Documentation Review:**

- Use the Task tool with subagent_type="documentation-reviewer" on all new/modified code
- Check: pattern compliance against `docs/*.md`, documentation gaps, clarity, verbosity, updates needed
- Report findings and wait for the user to address before continuing

**Design Compliance:**

- Confirm the implementation matches the intended design / plan reviewed by AGY
- If a `docs/plans/*.md` ADR exists for this work, cross-reference it

**Antipattern Scan:**

- Use the Task tool with subagent_type="antipattern-scanner" on all new/modified code
- Report findings and wait for the user to address before continuing

**Clean Code Review:**

- Use the Task tool with subagent_type="clean-code-reviewer" on all new/modified code
- Report findings and wait for the user to address before continuing

**Code Smell Detection:**

- Use the Task tool with subagent_type="code-smell-detector" on all new/modified code
- Report findings for the user's consideration

### 4. Test Quality Validation

- Scan test files for placeholder tests (`pass` only), fake/dummy data, or unjustified skips
- Confirm tests follow `docs/Testing.md` (pytest, one file per module, descriptive names + docstrings)
- Run `make test`
- If failures exist, STOP and require fixes before proceeding

### 5. Final Verification

- Run `make precommit` to verify all pre-commit hooks pass
- Require fixes before proceeding

## Success Criteria

- All issue requirements completed (if applicable)
- `make quality` passes (format + lint + typecheck)
- Code follows documented patterns
- No critical antipatterns detected (or acknowledged/fixed)
- Advisory reviews addressed or consciously deferred
- All tests passing (`make test`)
- Pre-commit hooks pass (`make precommit`)

## Final Output

1. Summary of checklist completion status
2. List of any remaining concerns or warnings
3. Confirmation that code is ready for PR, OR a list of items that need attention

## Important Notes

- **Fail Fast**: stop at the first major issue — don't continue if critical problems exist
- **Follow the Docs**: code should follow patterns in `docs/`
- **Advisory ≠ authoritative**: AGY and CodeRabbit are the deciding reviewers; conflicts go to William
