## Plan: Reach 100% Measured Line Coverage

Drive measured coverage from current 99% to 100% by adding targeted tests only (no production refactors), preserving current `.coveragerc` omits, and using a clean first pytest-cov run followed by `--cov-append` for iterative runs.

**Steps**
1. Baseline and lock target set: run `runpytest.sh` (which deletes `.coverage`, spins up 8 parallel DB shards with `--cov-append`, and finishes with `coverage html` + `coverage report`) to establish the authoritative uncovered list.
2. Phase 1 (largest gains first): add service-layer tests for webhook event/command handlers that currently contain the biggest uncovered blocks. *Blocks step 3 because these paths drive multiple dependent lines.*
3. Phase 2 (API resource edge paths): add REST resource tests for empty, invalid, and pagination/filter branches in webhook delivery endpoints. *Parallel with step 4 once step 2 is in progress.*
4. Phase 3 (single-line branch closures): add pinpoint tests for remaining 1-2 line misses in initialization/DI/forms/i18n/model helper modules. *Parallel with step 3.*
5. Re-run cumulative coverage workflow: first targeted run without `--cov-append`, subsequent focused runs with `--cov-append`, then a final full-suite verification pass to confirm stable 100%.
6. Stabilize and document: ensure tests are deterministic, no production code changes were needed, and capture final uncovered=none output for PR notes.

**Implementation detail by phase**
1. Baseline command workflow:
   1. Run `./runpytest.sh` — it already deletes `.coverage`, creates 8 parallel test databases, runs all splits with `--cov-append`, and ends with `coverage html` + `coverage report`.
   2. Capture the `coverage report --show-missing` output as the authoritative uncovered-lines list.
   3. For targeted iterative runs after adding new tests, run only the affected test file(s) with `--cov=project --cov-append` against an existing test DB, then call `coverage report --show-missing --precision=2` to verify gaps closed.
   4. Final verification: re-run `./runpytest.sh` from scratch to confirm `TOTAL ... 100%` under clean parallel conditions.
2. Phase 1 test additions (highest impact):
   1. Add/extend tests for app webhook event dispatch edge cases: unmapped event type, app missing, webhook not configured, successful payload/delivery creation.
   2. Add/extend tests for webhook delivery attempt command handler failure/retry branches and delivery-created-attempt handler edge paths.
   3. Add tests for celery command dispatcher behavior paths that are currently unhit.
3. Phase 2 API resource tests:
   1. Add list endpoint tests for invalid IDs, empty collections, pagination boundaries, filter/order permutations.
   2. Add delivery detail endpoint test for the missing not-found/single-item branch.
4. Phase 3 micro-gap tests:
   1. Cover import/branch misses in app bootstrap and DI container.
   2. Cover small uncovered branches in forms/i18n/model/repository helper logic.
5. Final verification:
   1. Execute full pytest coverage run from clean `.coverage`.
   2. Confirm measured line coverage is exactly 100%.
   3. Confirm omitted files remain omitted (by decision) and no new omit rules were introduced.

**Relevant files**
- `/Users/daniel/Projects/eventcally/.coveragerc` — preserve existing omit policy; do not expand omits.
- `/Users/daniel/Projects/eventcally/.vscode/settings.json` — confirms VS Code pytest coverage args include `--cov=project --cov-append` behavior.
- `/Users/daniel/Projects/eventcally/project/application/event_handlers/app_webhook_event_handler.py` — largest uncovered handler paths.
- `/Users/daniel/Projects/eventcally/project/application/command_handlers/attempt_to_deliver_webhook_command_handler.py` — retry/error branches.
- `/Users/daniel/Projects/eventcally/project/application/event_handlers/webhook_delivery_created_attempt_event_handler.py` — delivery-attempt event branches.
- `/Users/daniel/Projects/eventcally/project/infrastructure/celery_command_dispatcher.py` — dispatch paths missing tests.
- `/Users/daniel/Projects/eventcally/project/api/app/resources/app_webhook_delivery_attempt_list_resource.py` — list edge cases (largest API gap).
- `/Users/daniel/Projects/eventcally/project/api/app/resources/app_webhook_delivery_list_resource.py` — filter/order/list branches.
- `/Users/daniel/Projects/eventcally/project/api/app/resources/app_webhook_delivery_resource.py` — remaining single branch.
- `/Users/daniel/Projects/eventcally/project/__init__.py` — minor remaining bootstrap branch.
- `/Users/daniel/Projects/eventcally/project/container.py` — minor DI branch.
- `/Users/daniel/Projects/eventcally/tests/application/test_app_installation_webhook_event_handler.py` — primary pattern to mirror for event-handler tests.
- `/Users/daniel/Projects/eventcally/tests/conftest.py` — fixture behavior to reuse for deterministic DB-backed tests.

**Verification**
1. Run `./runpytest.sh` to obtain the fresh baseline `coverage report --show-missing` output.
2. After each phase, run only touched test modules with coverage append and verify that targeted missing lines disappear.
3. Before completion, run `./runpytest.sh` end-to-end and verify `TOTAL ... 100%` in `coverage report`.
4. Open html coverage and spot-check previously problematic modules now show 100% lines covered.
5. Run `pre-commit run --all-files` to ensure style/lint remains clean after test additions.

**Decisions**
- Included: measured files only (respect current `.coveragerc` omits).
- Included: 100% line coverage requirement; branch coverage not targeted.
- Included: test-only approach preferred; avoid production refactors unless absolutely unavoidable.
- Excluded: removing/altering existing omit policy to game coverage.

**Further Considerations**
1. If one or two lines remain unreachable due to framework import-time behavior, prefer a focused initialization-path test before considering `pragma` or omit changes.
2. If `--cov-append` introduces confusing totals during iteration, re-run `./runpytest.sh` from scratch to re-establish a clean baseline.
