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
- **Visual Baseline** - For UI migrations to Vue 3: the pages, states and viewports to match,
  and where the "before" screenshots are
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

### Visual Baseline (UI migration to Vue 3 only)

> **⚠️ Do NOT start Phase 3 until the "before" screenshots exist.** Once the old UI is
> replaced, the baseline is gone.

- If the plan's Visual Baseline section points to existing screenshots, check that every
  page × state × viewport is there.
- Otherwise start the app on the **unchanged** code and take them now: full-page screenshots
  for desktop `1280×800` and mobile `390×844` via the Playwright MCP (`browser_resize` +
  `browser_take_screenshot`) or a throwaway `npx playwright` script. Save them to
  `.agents/screenshots/{YYYY-MM-DD}-{plan-name}/before-{desktop|mobile}-{state}.png`.
- If the task turns out to migrate a UI but the plan has no Visual Baseline section, capture
  one anyway (derive pages and states from the plan) and note it as a deviation.

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
- **Never hand-edit `*_generated.py`** — change the YAML in `.scripts/codegen/config/` and run
  `python .scripts/codegen/generate.py`; put custom logic in the handwritten sibling
- **Check integration**: do imports resolve? Do callers still work? Is a new command/event
  handler registered in the DI container (`project/container.py`)? Is a new Celery task
  imported in `project/presentation/tasks/celery_tasks.py`? Is a DB schema change accompanied by an Alembic
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

```

Then run the tests **in tiers, cheapest first, failing fast**. Stop at the first failing
tier, fix, and re-run that tier before moving on.

**Collect the changed files** (committed on the branch + uncommitted + untracked):

```bash
{ git diff --name-only main...HEAD; git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u
```

**Tier 1 — unit tests (always, no services, seconds):**

```bash
pytest tests/unit -x -q --no-cov
```

**Tier 2 — frontend (only if `frontend/` or BFF models changed):**

```bash
npm run typecheck --prefix frontend && npm test --prefix frontend -- --bail 1
# BFF pydantic models changed → regenerate and check for drift
python -m project.presentation.bff.openapi > frontend/openapi.json && npm run gen:api --prefix frontend
git diff --exit-code frontend/openapi.json frontend/src/api/schema.d.ts
```

**Tier 3 — targeted integration tests (if anything outside `tests/unit` / `frontend/` changed):**
the mirrored test files of every changed module (`project/<path>/<mod>.py` →
`tests/integration/<path>/test_<mod>.py`), plus every new or changed test file, plus the
tests of direct callers you touched (e.g. the view/API tests for a changed handler).

```bash
./runtests.sh --splits 1 --group 1 -- <test paths> -x
# coverage of the changed modules (inside the container: the data file holds /app paths)
docker compose -f docker-compose.test.yml run --rm pytest \
  coverage report -m --data-file=.coverage.1 --include='project/<changed path>/*'
```

New or changed modules must show no missed lines here — CI fails below 100% total coverage.

**Tier 4 — full suite (`./runtests.sh`, parallel, ~minutes, enforces 100% coverage):**

| Changes touch… | Action |
| ------- | -------- |
| Cross-cutting code: `project/container.py`, `project/factory.py`, `project/config.py`, `project/infrastructure/models/`, migrations, codegen YAML / `*_generated.py`, `message_bus.py` / `query_bus.py`, base classes (`commands/base.py`, `abstract_*`), `project/presentation/shared/`, `project/shared/`, `tests/integration/conftest.py` / `seeder.py` / `base_test.py`, `pyproject.toml` / `uv.lock`, templates or Jinja filters shared across pages | Run `./runtests.sh` without asking |
| Only modules whose tests Tier 3 already ran | Ask the user (AskUserQuestion): "Run the full suite now (~minutes), or leave it to CI?" — recommend leaving it to CI |
| Running autonomously / told not to ask | Apply the first row; when unsure, run the full suite |

Record in the report which tiers ran, and if Tier 4 was skipped, that CI will run it.

**Every tier that runs must pass with zero errors.**

### Write Tests

You MUST write tests for new code:

- Every new command handler / function needs at least one test in the matching suite
  at the mirrored path (`tests/unit/application/`, `tests/unit/domain/`,
  `tests/integration/presentation/{api,bff,web}/`, `tests/integration/infrastructure/`)
- Error cases and edge cases need tests
- Update existing tests if behavior changed
- **Assert through the architecture** — exercise command/event flows via the message bus and
  repository interfaces rather than bypassing them; test routes via the `client` fixture
- Reuse fixtures from `tests/integration/conftest.py` (`app`, `db`, `client`, `seeder`, `utils`,
  `container`, `message_bus`) and base classes in `tests/integration/base_test.py`
- Note: `tests/unit/` runs with no external services; other suites
  need PostGIS + Redis

**If tests fail:**

1. Determine: bug in implementation or test?
2. Fix the actual issue
3. Re-run the failing tier (or just the failing tests with `-x`) until green, then continue
   with the next tier

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

### REQUIRED for UI migrations to Vue 3: Visual Alignment

- [ ] Take "after" screenshots of the same pages, states and viewports as the baseline
      (`.../after-{desktop|mobile}-{state}.png`, same folder)
- [ ] Compare each before/after pair (Read both images) for layout, order, spacing, sizes,
      typography, colors, icons, labels and responsive behavior (stacking, hidden columns,
      collapsed filters on mobile)
- [ ] Adjust the Vue UI to match the old UI, re-take the "after" screenshot, repeat until
      desktop **and** mobile match
- [ ] Only keep a difference when it is intentional (e.g. a fixed bug or a Bootstrap 5 /
      bootstrap-vue-next default that can't reasonably be matched) — list each one with its
      rationale in the report

Don't proceed to Phase 5 while an unexplained difference remains.

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
| Unit tests (Tier 1) | ✅ ({N} passed) |
| Frontend (Tier 2) | ✅ / N/A |
| Targeted integration + coverage (Tier 3) | ✅ ({N} passed, changed modules 100%) / N/A |
| Full suite (Tier 4) | ✅ / skipped — left to CI ({reason}) |

## Files Changed

| File | Action | Lines |
| ------ | -------- | ------- |
| `project/application/commands/foo.py` | CREATE | +{N} |
| `project/container.py` | UPDATE | +{N}/-{M} |

## Deviations from Plan

{List any deviations with rationale, or "None"}

## Visual Alignment

{UI migrations to Vue 3 only — otherwise "N/A"}

| Page / state | Viewport | Before | After | Match |
| ------ | -------- | ------ | ----- | ----- |
| {page / state} | desktop | `before-desktop-{state}.png` | `after-desktop-{state}.png` | ✅ / {intentional difference + rationale} |
| {page / state} | mobile | `before-mobile-{state}.png` | `after-mobile-{state}.png` | ✅ / {intentional difference + rationale} |

Screenshots: `.agents/screenshots/{YYYY-MM-DD}-{plan-name}/`

## Tests Written

| Test File | Test Cases |
| ----------- | ------------ |
| `tests/unit/application/test_foo.py` | {list} |
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

- Don't create the PR here: `/pr` does that and puts `Fixes #<number>` in the body, so
  merging closes the issue.
- If the work was done directly on `main` (no PR), close it:
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
| Visual alignment (desktop + mobile) | ✅ / N/A |

### Files Changed

- {N} files created
- {M} files updated
- {K} tests written

### Deviations

{Summary or "Implementation matched the plan."}

### Artifacts

- Report: `.agents/reports/{YYYY-MM-DD}-{name}-report.md`
- Screenshots (UI migrations): `.agents/screenshots/{YYYY-MM-DD}-{name}/`
- Plan archived: `.agents/plans/completed/`

### GitHub Issue

{If issue was updated: "Commented on #{number}; will auto-close via PR 'Fixes #{number}'."
Otherwise: "No GitHub issue linked."}

### Next Steps

1. Review the report
2. `/pr` — creates the PR (with `Fixes #{number}`) and watches the checks
3. `/merge` when approved
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
