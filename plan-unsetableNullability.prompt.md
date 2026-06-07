## Plan: Split Unsetable Nullability

Introduce two explicit patch-field aliases and migrate the codebase to use them consistently: `Unsetable[T]` for "unset or value" and `NullableUnsetable[T]` for "unset or value or None". The recommended approach is to make this a real validation change, not just a typing cleanup, so non-null patch fields reject `None` at Pydantic validation time while nullable patch fields continue to support explicit clearing.

**Steps**
1. Phase 1: Core type split. Update `/Users/daniel/Projects/eventcally/project/domain/types/unsetable.py` to define two distinct aliases and validation schemas. Recommended implementation: keep the current adapter pattern but centralize schema construction in one small helper so the only difference is whether `core_schema.none_schema()` is included. `Unsetable[T]` should validate `_Unset | T`; `NullableUnsetable[T]` should validate `_Unset | T | None`. Keep serialization behavior unchanged.
2. Export the new alias from `/Users/daniel/Projects/eventcally/project/domain/types/__init__.py` and keep the existing `unset`/`UnsetField` API unchanged. This keeps call sites small and avoids introducing a second field factory.
3. Phase 2: Migrate handwritten command DTOs. Replace any field that should allow explicit clearing with `NullableUnsetable[...]` in `/Users/daniel/Projects/eventcally/project/application/commands/update_event_command.py`, `/Users/daniel/Projects/eventcally/project/application/commands/update_event_place_command.py`, `/Users/daniel/Projects/eventcally/project/application/commands/update_event_organizer_command.py`, and `/Users/daniel/Projects/eventcally/project/application/commands/update_app_command.py`. Keep truly non-null patch fields on `Unsetable[...]`. This step depends on step 1.
4. While updating commands, use the model YAML files only as the nullability source of truth for persistent fields, not as direct edit targets unless a schema is actually wrong. Audit `/Users/daniel/Projects/eventcally/codegen/config/models/event.yml`, `/Users/daniel/Projects/eventcally/codegen/config/models/oauth2_client.yml`, `/Users/daniel/Projects/eventcally/codegen/config/models/event_organizer.yml`, `/Users/daniel/Projects/eventcally/codegen/config/models/event_place.yml`, and `/Users/daniel/Projects/eventcally/codegen/config/models/webhook.yml` to decide which patch fields must stay nullable. Do not edit `*_generated.py` files.
5. Phase 3: Migrate handwritten model update signatures and closely related domain events. Update the patch/update method annotations in `/Users/daniel/Projects/eventcally/project/models/event.py`, `/Users/daniel/Projects/eventcally/project/models/event_place.py`, `/Users/daniel/Projects/eventcally/project/models/event_organizer.py`, `/Users/daniel/Projects/eventcally/project/models/oauth.py`, `/Users/daniel/Projects/eventcally/project/models/webhook.py`, `/Users/daniel/Projects/eventcally/project/models/image.py`, and `/Users/daniel/Projects/eventcally/project/models/location.py` so they mirror the command-layer split. Then review `/Users/daniel/Projects/eventcally/project/domain/events/event_updated.py`, `/Users/daniel/Projects/eventcally/project/domain/events/event_place_updated.py`, `/Users/daniel/Projects/eventcally/project/domain/events/event_organizer_updated.py`, and `/Users/daniel/Projects/eventcally/project/domain/events/app_updated.py` to ensure any nested changed-value payloads that can be cleared are also marked nullable where appropriate. This step depends on steps 1 and 3.
6. Phase 4: Review webhook payload mappers and nested updated payload models for `unset` vs `None` propagation. Verify `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/nested/image_updated.py`, `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/nested/location_updated.py`, `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/event_place_updated_payload.py`, and `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/event_organizer_updated_payload.py` still preserve the three states correctly after the type split. This step can run in parallel with the latter half of step 5 once the aliases exist.
7. Phase 5: Add focused regression tests for the new validation boundary. Add one dedicated test module for the type aliases, for example under `/Users/daniel/Projects/eventcally/tests/`, that proves `Unsetable[T]` rejects `None` and `NullableUnsetable[T]` accepts `None`. Then extend existing model/view/API tests to cover both "field omitted" and "field explicitly set to null/None" for representative nullable fields such as event description, event previous_start_date, organizer contact fields if they are intended to be clearable, OAuth client description/app_permissions, and webhook secret. This step depends on steps 1 through 6.
8. Phase 6: Run a consistency sweep. Remove any remaining `Unsetable[Optional[...]]` patterns across the repo, verify imports are normalized, and confirm the remaining plain `Unsetable[...]` usages are intentionally non-null patch fields. This final pass depends on all earlier steps.

**Relevant files**
- `/Users/daniel/Projects/eventcally/project/domain/types/unsetable.py` — split the aliases and make validation behavior distinct.
- `/Users/daniel/Projects/eventcally/project/domain/types/__init__.py` — export `NullableUnsetable`.
- `/Users/daniel/Projects/eventcally/project/application/commands/update_event_command.py` — largest command DTO migration surface.
- `/Users/daniel/Projects/eventcally/project/application/commands/update_event_place_command.py` — patch fields for place updates.
- `/Users/daniel/Projects/eventcally/project/application/commands/update_event_organizer_command.py` — organizer contact/logo/location patch fields.
- `/Users/daniel/Projects/eventcally/project/application/commands/update_app_command.py` — OAuth client patch fields plus nested webhook.
- `/Users/daniel/Projects/eventcally/project/models/event.py` — event update signature and update semantics.
- `/Users/daniel/Projects/eventcally/project/models/event_place.py` — place update signature.
- `/Users/daniel/Projects/eventcally/project/models/event_organizer.py` — organizer update signature.
- `/Users/daniel/Projects/eventcally/project/models/oauth.py` — OAuth client update signature.
- `/Users/daniel/Projects/eventcally/project/models/webhook.py` — representative nested owned object that already distinguishes `unset` and `None` at runtime.
- `/Users/daniel/Projects/eventcally/project/models/image.py` — nullable nested image-field updates.
- `/Users/daniel/Projects/eventcally/project/models/location.py` — nullable nested location-field updates.
- `/Users/daniel/Projects/eventcally/project/domain/events/event_updated.py` — update event payload nullability alignment.
- `/Users/daniel/Projects/eventcally/project/domain/events/event_place_updated.py` — nested place changed values.
- `/Users/daniel/Projects/eventcally/project/domain/events/event_organizer_updated.py` — nested organizer changed values.
- `/Users/daniel/Projects/eventcally/project/domain/events/app_updated.py` — nested webhook changed values.
- `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/nested/image_updated.py` — verify `unset`/`None` payload mapping.
- `/Users/daniel/Projects/eventcally/project/application/webhooks/payloads/nested/location_updated.py` — verify `unset`/`None` payload mapping.
- `/Users/daniel/Projects/eventcally/codegen/config/models/event.yml` — reference for persisted field nullability decisions.
- `/Users/daniel/Projects/eventcally/codegen/config/models/oauth2_client.yml` — reference for persisted field nullability decisions.
- `/Users/daniel/Projects/eventcally/codegen/config/models/event_organizer.yml` — reference for persisted field nullability decisions.
- `/Users/daniel/Projects/eventcally/codegen/config/models/event_place.yml` — reference for persisted field nullability decisions.
- `/Users/daniel/Projects/eventcally/codegen/config/models/webhook.yml` — reference for persisted field nullability decisions.
- `/Users/daniel/Projects/eventcally/tests/test_webhook_model.py` — existing direct coverage of `unset` vs `None` on nested objects.
- `/Users/daniel/Projects/eventcally/tests/test_models.py` — existing model-level `photo=None` coverage.
- `/Users/daniel/Projects/eventcally/tests/views/test_event.py` — representative end-to-end event update coverage.
- `/Users/daniel/Projects/eventcally/tests/views/test_event_place.py` — representative place update coverage.
- `/Users/daniel/Projects/eventcally/tests/views/test_organizer.py` — representative organizer update coverage.
- `/Users/daniel/Projects/eventcally/tests/views/test_oauth2_client.py` — representative OAuth client update coverage.

**Verification**
1. Add and run a focused alias test proving `Unsetable[T]` rejects `None` while `NullableUnsetable[T]` accepts `None`.
2. Run targeted regression tests: `pytest tests/test_webhook_model.py tests/test_models.py tests/views/test_event.py tests/views/test_event_place.py tests/views/test_organizer.py tests/views/test_oauth2_client.py`.
3. Run targeted API tests for any update endpoints that accept JSON nulls, especially event, organizer, place, and app/webhook update flows, if those suites are the entry point for command validation.
4. Run a repo-wide search to confirm there are no remaining `Unsetable[Optional[` annotations and no accidental `NullableUnsetable` omissions on intentionally clearable fields.
5. If any YAML schema had to change for nullability correctness, regenerate with `python codegen/generate.py` and rerun the focused test set above.

**Decisions**
- Accepted requirement: `Unsetable[T]` should reject `None` at validation time; `NullableUnsetable[T]` should allow explicit clearing with `None`.
- Scope includes handwritten command DTOs, handwritten model update signatures, affected domain/webhook payload types, and focused tests.
- Scope excludes direct edits to generated `*_generated.py` files.
- Recommended implementation detail: prefer a small shared schema-builder helper over duplicating adapter logic, but keep two public aliases because the semantic distinction is the point of the migration.

**Further Considerations**
1. Organizer/email/phone/fax and similar plain `string` YAML fields need an explicit product decision during implementation: if the app should support clearing them, migrate them to `NullableUnsetable[str]`; if not, keep them as `Unsetable[str]` and add validation tests that `null` is rejected.
2. List-valued patch fields such as `redirect_uris`, `app_permissions`, `category_ids`, and `custom_category_ids` need explicit handling rules: use `[]` for clear-to-empty and reserve `None` only for fields that truly have a null state.
3. Nested owned objects already encode three states at runtime (`unset`, `None`, value). The implementation should preserve that behavior exactly and only tighten schema validation where a field is intentionally non-nullable.
