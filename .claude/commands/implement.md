---
description: Execute an implementation plan with validation loops
argument-hint: <path/to/plan.md>
---

# Implement Plan

**Plan**: $ARGUMENTS

## Your Mission

Execute the plan end-to-end with rigorous self-validation.

**Core Philosophy**: Validation loops catch mistakes early. Run checks after every change. Fix issues immediately.

**Golden Rule**: If validation fails, fix it before moving on. Never accumulate broken state.

---

## Phase 1: LOAD

### Read the Plan

Load the plan file and extract:

- **Summary** - What we're building
- **Patterns to Mirror** - Code to copy from
- **Files to Change** - CREATE/UPDATE list
- **Tasks** - Implementation order
- **Validation Commands** - How to verify
- **GitHub Issue** - Check the plan's Metadata table for a GitHub Issue number (e.g. `#11`).
  If present, this issue will be updated/closed after implementation is complete.

**If plan not found:**

```text
Error: Plan not found at $ARGUMENTS
Create a plan first: /plan "feature description"
```

---

## Phase 2: PREPARE

### Git State

```bash
git branch --show-current
git status
```

> Note: the PR base branch for this repo is `main`.

| State | Action |
| ------- | -------- |
| On `main`, clean | Create branch: `git checkout -b issue/{plan-name}` (if the plan has a linked GitHub Issue number, prefix the plan name with it: `git checkout -b issue/{issue-number}-{plan-name}`) |
| On `main`, dirty | STOP: "Stash or commit changes first" |
| On feature branch | Use it |

---

## Phase 3: EXECUTE

**For each task in the plan:**

### 3.1 Verify Assumptions

Before writing any code for a task:

- **Read the target file** you're about to create or modify
- **Read adjacent files** — files it imports from, and files that import it
- **Verify the plan's references** — do the commands, handlers, models, repositories, routes,
  or tasks the plan mentions actually exist? Do they match the plan's expectations?
- **If assumptions are wrong**, adapt your approach before implementing. Document what differs.

### 3.2 Implement

- Read the **MIRROR** file reference and understand the pattern to follow
- Make the change as specified in the plan
- **Respect the DDD import layering** (`domain` ← `application` ← `infrastructure`) — never
  import "up" a layer; check `project/domain/allowed_imports.cfg` and
  `project/application/allowed_imports.cfg` before adding imports
- **Never hand-edit `*_generated.py`** — change the YAML in `codegen/config/` and run
  `python codegen/generate.py`; put custom logic in the handwritten sibling
- **Check integration**: do imports resolve? Do callers still work? Is a new command/event
  handler registered in the DI container (`project/container.py`)? Is a new Celery task
  imported in `project/celery_tasks.py`? Is a DB schema change accompanied by an Alembic
  migration (`flask db migrate`)?

### 3.3 Validate Immediately

**After EVERY task**, format, lint, and check import layering on the changed files:

```bash
isort <changed files> && black <changed files> && flake8 <changed files> && lint-imports
```

**If it fails:**

1. Read the error
2. Fix the issue (`isort <file>` / `black <file>` to autoformat)
3. Re-run validation
4. Only proceed when passing

### 3.4 Track Progress

```text
Task 1: CREATE project/application/commands/foo.py ✅
Task 2: UPDATE project/container.py ✅
```

**If you deviate from the plan**, document what changed and why.

---

## Phase 4: VALIDATE

### Run All Checks

```bash
# Format & lint (order matters — CI checks)
isort . && black . && flake8 && lint-imports && \
  python .scripts/module_import_whitelist.py project/domain project/application
# or: pre-commit run --all-files

# Tests (most suites need PostGIS + Redis)
docker-compose -f docker-compose.test.services.yml up -d
pytest
```

**All must pass with zero errors.**

### Write Tests

You MUST write tests for new code:

- Every new command handler / function needs at least one test in the matching suite
  (`tests/application/`, `tests/domain/`, `tests/api/`, `tests/views/`, `tests/infrastructure/`)
- Error cases and edge cases need tests
- Update existing tests if behavior changed
- **Assert through the architecture** — exercise command/event flows via the message bus and
  repository interfaces rather than bypassing them; test routes via the `client` fixture
- Reuse fixtures from `tests/conftest.py` (`app`, `db`, `client`, `seeder`, `utils`,
  `container`, `message_bus`) and base classes in `tests/base_test.py`
- Note: `tests/application/` and `tests/domain/` run with no external services; other suites
  need PostGIS + Redis

**If tests fail:**

1. Determine: bug in implementation or test?
2. Fix the actual issue
3. Re-run until green

### REQUIRED: End-to-End Verification

> **⚠️ Do NOT proceed to Phase 5 (Report) until all E2E steps below pass.**

Re-read the plan and find the end-to-end testing section. Execute every E2E test listed in
the plan as a checklist:

- [ ] Bring up the app / dependencies (`docker-compose up --build`, or local Postgres/PostGIS
      + Redis with `flask db upgrade` then `flask run --host 0.0.0.0`)
- [ ] For EACH end-to-end test in the plan:
  - [ ] Execute the test exactly as described
  - [ ] Verify the expected outcome matches the plan
  - [ ] If it fails: fix the issue, re-run, confirm it passes
- [ ] Confirm all E2E tests pass before proceeding

**If the plan has no E2E tests**, perform a basic smoke test: start the app (or hit the
affected route/API/command/task), exercise the new/changed behavior, verify it works. For UI
flows, the Playwright suite (`npx playwright test`) is available.

**This is a hard gate.** You cannot report the implementation as complete until E2E
verification passes. Static checks and unit tests alone are never sufficient.

---

## Phase 5: REPORT

### Create Report

**Output path**: `.agents/reports/{YYYY-MM-DD}-{plan-name}-report.md`

Every generated markdown file **must** be prefixed with the current date in `YYYY-MM-DD`
form. Use today's date (not the plan's date), and if the plan file name already carries a
date prefix, strip it from `{plan-name}` so the prefix isn't duplicated. Get the date from
the system — never guess it:

```bash
mkdir -p .agents/reports
date +%F   # e.g. 2026-09-01 -> .agents/reports/2026-09-01-my-feature-report.md
```

```markdown
# Implementation Report

**Plan**: `{plan-path}`
**Branch**: `{branch-name}`
**Status**: COMPLETE

## Summary

{Brief description of what was implemented}

## Tasks Completed

| # | Task | File | Status |
| --- | ------ | ------ | -------- |
| 1 | {description} | `project/application/commands/foo.py` | ✅ |
| 2 | {description} | `project/container.py` | ✅ |

## Validation Results

| Check | Result |
| ------- | -------- |
| isort / black | ✅ |
| flake8 | ✅ |
| lint-imports / import-whitelist | ✅ |
| Tests | ✅ ({N} passed) |

## Files Changed

| File | Action | Lines |
| ------ | -------- | ------- |
| `project/application/commands/foo.py` | CREATE | +{N} |
| `project/container.py` | UPDATE | +{N}/-{M} |

## Deviations from Plan

{List any deviations with rationale, or "None"}

## Tests Written

| Test File | Test Cases |
| ----------- | ------------ |
| `tests/application/test_foo.py` | {list} |
```

### Archive Plan

```bash
mkdir -p .agents/plans/completed
mv $ARGUMENTS .agents/plans/completed/
```

---

## Phase 6: UPDATE GITHUB ISSUE (if issue specified in plan)

**This phase is mandatory if the plan's Metadata table contains a GitHub Issue number.**
Skip only if the GitHub Issue field is "N/A" or absent.

### 6.1 Add Implementation Comment

Post a summary comment on the issue:

```bash
gh issue comment <number> --body "<summary>"
```

The summary should include:

- What was implemented
- Branch name
- Files created/updated (count)
- Tests written (count)
- Any deviations from the plan
- Path to the implementation report file

### 6.2 Link the Work

- If a PR is created (Phase 7), reference the issue in the PR body with a closing keyword
  (`Closes #<number>` / `Fixes #<number>`) so merging auto-closes it — this repo's history
  uses `Fixes #N` in commits/PRs.
- If no PR yet and the work is complete on `main`, you may close it directly:
  `gh issue close <number> --comment "Implemented in {branch/commit}"`.

---

## Phase 7: OUTPUT

```markdown
## Implementation Complete

**Plan**: `{plan-path}`
**Branch**: `{branch-name}`
**Status**: ✅ Complete

### Validation

| Check | Result |
| ------- | -------- |
| isort / black | ✅ |
| flake8 | ✅ |
| lint-imports / import-whitelist | ✅ |
| Tests | ✅ |

### Files Changed

- {N} files created
- {M} files updated
- {K} tests written

### Deviations

{Summary or "Implementation matched the plan."}

### Artifacts

- Report: `.agents/reports/{YYYY-MM-DD}-{name}-report.md`
- Plan archived: `.agents/plans/completed/`

### GitHub Issue

{If issue was updated: "Commented on #{number}; will auto-close via PR 'Fixes #{number}'."
Otherwise: "No GitHub issue linked."}

### Next Steps

1. Review the report
2. Create PR against `main`: `gh pr create --base main` (include `Fixes #{number}` in body)
3. Merge when approved
```

---

## Handling Failures

| Failure | Action |
| --------- | -------- |
| flake8 fails | Read error, fix issue, re-run |
| lint-imports / import-whitelist fails | Fix the layering violation (don't import "up" a layer) |
| Tests fail | Fix implementation or test, re-run |
| Formatting fails | Run `isort .` and `black .`, then re-check |
| App won't start | Check required env vars (`DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings) and PostGIS + Redis availability |
