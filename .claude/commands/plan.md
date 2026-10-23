---
description: Create implementation plan with codebase analysis
argument-hint: <feature description | path/to/prd.md>
---

# Implementation Plan Generator

**Input**: $ARGUMENTS

## Objective

Transform the input into a battle-tested implementation plan through codebase exploration and pattern extraction.

**Core Principle**: PLAN ONLY - no code written. Create a context-rich document that enables one-pass implementation.

**Order**: CODEBASE FIRST. Solutions must fit existing patterns.

---

## Phase 1: PARSE

### Determine Input Type

| Input | Action |
| ------- | -------- |
| `.prd.md` file | Read PRD, extract next pending phase |
| Other `.md` file | Read and extract feature description |
| Free-form text | Use directly as feature input |
| Blank | Use conversation context |

### Extract Feature Understanding

- **Problem**: What are we solving?
- **User Story**: As a [user], I want to [action], so that [benefit]
- **Type**: NEW_CAPABILITY / ENHANCEMENT / REFACTOR / BUG_FIX
- **Complexity**: LOW / MEDIUM / HIGH
- **GitHub Issue**: If a GitHub issue number (e.g. `#11`) is available in the conversation
  context — from a prior `/prime` command, user mention, or PRD — capture it. This is
  optional but should be included in the plan metadata when available so that `/implement`
  can update and close the issue after completion.
- **UI migration to Vue 3**: Does the task replace an existing UI (Jinja template, legacy JS)
  with a Vue 3 page? If so, the plan **must** include a visual baseline (see Phase 2 and the
  "Visual Baseline" section of the plan template) so the new UI can be aligned to the old one.

---

## Phase 2: EXPLORE

### Study the Codebase

Use the Explore agent to find:

1. **Similar implementations** - analogous features with file:line references
2. **Naming conventions** - actual examples from the codebase (snake_case modules/functions)
3. **Error handling patterns** - how errors are raised/handled in views, API resources, handlers
4. **DDD flow** - how a change moves through the layers: view/API → application command →
   command handler → repository (`project/domain` via `project/infrastructure`); events via
   `project/application/message_bus.py`
5. **Data access** - SQLAlchemy repositories in `project/infrastructure/repositories/`; note
   whether the model is codegen-backed (`*_generated.py` from `.scripts/codegen/config/`)
6. **Test patterns** - `tests/integration/conftest.py` fixtures and `tests/integration/base_test.py` base classes;
   which suites need PostGIS + Redis vs the `application/` + `domain/` suites that don't

### Document Patterns

| Category | File:Lines | Pattern |
| ---------- | ------------ | --------- |
| NAMING | `project/application/commands/...:10-15` | {pattern description} |
| ERRORS | `project/api/...:20-30` | {pattern description} |
| COMMAND/HANDLER | `project/application/command_handlers/...:1-30` | {command → handler → repo flow} |
| DATA | `project/infrastructure/repositories/...:1-10` | {repository / codegen model} |
| TESTS | `tests/.../test_...:1-25` | {pattern description} |

### Capture the Visual Baseline (UI migration to Vue 3 only)

While the old UI still exists, define and capture what the new UI must match:

1. **List the pages and states** to compare: every affected route, plus the relevant states
   (empty / filled list, validation errors, logged-in vs anonymous, open dropdowns / modals /
   collapsed filters, long content).
2. **Fix the viewports**: desktop `1280×800` and mobile `390×844`.
3. **Take the "before" screenshots** of every page × state × viewport (full page) with the
   Playwright MCP (`browser_resize` + `browser_take_screenshot`) or a throwaway
   `npx playwright` script against the running app. Save them to
   `.agents/screenshots/{YYYY-MM-DD}-{kebab-case-name}/before-{desktop|mobile}-{state}.png`
   (same date and name as the plan file).
4. **If the app can't be run now**, still write the list into the plan — `/implement` then
   captures the baseline before touching any code.

---

## Phase 3: DESIGN

### Map the Changes

- What files need to be created?
- What files need to be modified?
- Is a model codegen-backed? If so, edit the YAML in `.scripts/codegen/config/` and regenerate
  (`python .scripts/codegen/generate.py`) — never hand-edit `*_generated.py`.
- New command/event? Register the handler in the DI container (`project/container.py`).
- New Celery task? Register it in `project/presentation/tasks/celery_tasks.py`.
- Any DB schema change → new Alembic migration (`flask db migrate`, then review — PostGIS
  diffs sometimes need manual correction).
- Do the changes respect the import layering (`domain` ← `application` ← `infrastructure`)?
- What's the dependency order?

### Identify Risks

| Risk | Mitigation |
| ------ | ------------ |
| {potential issue} | {how to handle} |

---

## Phase 4: GENERATE

### Create Plan File

**Output path**: `.agents/plans/{YYYY-MM-DD}-{kebab-case-name}.plan.md`

Every generated markdown file **must** be prefixed with the current date in `YYYY-MM-DD`
form, so plans sort chronologically. Get the date from the system — never guess it:

```bash
mkdir -p .agents/plans
date +%F   # e.g. 2026-09-01 -> .agents/plans/2026-09-01-my-feature.plan.md
```

````markdown
# Plan: {Feature Name}

## Summary

{One paragraph: What we're building and approach}

## User Story

As a {user type}
I want to {action}
So that {benefit}

## Metadata

| Field | Value |
| ------- | ------- |
| Type | {type} |
| Complexity | {LOW/MEDIUM/HIGH} |
| Systems Affected | {list} |
| GitHub Issue | {issue number if available, e.g. #11, or "N/A"} |

---

## Patterns to Follow

### Naming
```python
# SOURCE: {file:lines}
{actual code snippet}
```

### Command / Handler
```python
# SOURCE: {file:lines}
{actual code snippet}
```

### Tests
```python
# SOURCE: {file:lines}
{actual code snippet}
```

---

## Files to Change

| File | Action | Purpose |
| ------ | -------- | --------- |
| `project/application/commands/foo.py` | CREATE | {why} |
| `project/application/command_handlers/foo.py` | CREATE | {why} |
| `project/container.py` | UPDATE | {register handler} |

---

## Visual Baseline

{Only for UI migrations to Vue 3 — otherwise write "N/A"}

| Page / route | States | Viewports | Before screenshots |
| ------ | -------- | --------- | --------- |
| `/manage/...` | {empty, filled, errors, ...} | desktop 1280×800, mobile 390×844 | `.agents/screenshots/{YYYY-MM-DD}-{name}/` or "to capture in /implement" |

---

## Tasks

Execute in order. Each task is atomic and verifiable.

### Task 1: {Description}

- **File**: `project/application/commands/foo.py`
- **Action**: CREATE / UPDATE
- **Implement**: {what to do}
- **Mirror**: `project/application/commands/{existing}.py:lines` - follow this pattern
- **Validate**: `flake8 project/application/commands/foo.py && lint-imports`

### Task 2: {Description}

- **File**: `project/container.py`
- **Action**: UPDATE
- **Implement**: {register the new handler}
- **Mirror**: `project/container.py:lines`
- **Validate**: `pytest tests/unit/application -k foo`

{Continue for each task...}

---

## Validation

```bash
# Format & lint (order matters — CI checks)
isort . && black . && flake8 && lint-imports && \
  python .scripts/module_import_whitelist.py project/domain project/application
# or: pre-commit run --all-files

# Tests (most suites need PostGIS + Redis; start them first if not running)
docker compose -f docker-compose.test.yml up -d --wait
pytest
```

---

## Acceptance Criteria

- [ ] All tasks completed
- [ ] isort / black / flake8 / lint-imports / import-whitelist pass
- [ ] Tests pass
- [ ] Follows existing patterns (DDD import layering respected; no hand-edited `*_generated.py`)
- [ ] UI migration to Vue 3 only: new UI matches the visual baseline on desktop and mobile
      (intentional differences listed with rationale)
````

---

## Phase 5: OUTPUT

```markdown
## Plan Created

**File**: `.agents/plans/{YYYY-MM-DD}-{name}.plan.md`

**Summary**: {2-3 sentence overview}

**Scope**:
- {N} files to CREATE
- {M} files to UPDATE
- {K} total tasks

**Key Patterns**:
- {Pattern 1 with file:line}
- {Pattern 2 with file:line}

**Next Step**: Review the plan, then implement tasks in order.
```
