---
description: "Scaffold a new read-side query with read model, read repository and handler, and wire up the query bus"
argument-hint: "Query name (e.g., ListEventOrganizers, GetEventOrganizer)"
---

# Add DDD Query

Scaffold a read path that replaces direct ORM access (`Model.query`, `get_or_404`,
`paginate()`, `project/services` read helpers) in views, the API and `project/modular`.

Reads go: view / API → `query_bus.handle(query)` → query handler → read repository →
read-only session. The bus has no unit of work, no commit and no event dispatch.

## Pre-Flight Checks

1. **Verify the query doesn't exist**: search [`project/application/queries/`](../../project/application/queries/)
   and [`project/application/query_handlers/`](../../project/application/query_handlers/).
2. **Shape the result for the use case**: a list row and a detail page are different read
   models (`EventOrganizerListItemReadModel`, `EventOrganizerDetailReadModel`), not one
   model per entity. List exactly the attributes the template / marshmallow schema reads.
3. **Decide the not-found contract**: single-object queries return `Optional[...]` and the
   delivery code turns `None` into a 404. Do not raise `NotFoundError` — the API maps
   `BaseError` to 400.

## Steps

### 1. Read model(s)

Location: `project/application/read_models/<entity>_read_models.py`

```python
from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class EventOrganizerListItemReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
```

- Frozen, hand-written, no codegen. Reuse the shared pieces: `LocationReadModel`,
  `ImageReadModel` (+ `LicenseRefReadModel`, `get_hash()` for `url_for_image`) and
  `OrganizationRefReadModel` in `project/application/read_models/`.
- Keep the ORM value types the schemas dump: numeric columns stay `Decimal` (so
  `NumericStr` prints the same digits), timestamps stay naive `datetime`.
- Keep the attribute names the existing marshmallow schemas and templates read, so delivery
  code renders read models unchanged (duck typing).

### 2. Query

Location: `project/application/queries/<snake_case_name>_query.py`

```python
from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import TrackableCriteria
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListEventOrganizersQuery(Query[Optional[Page[EventOrganizerListItemReadModel]]]):
    admin_unit_id: ObjectId
    keyword: Optional[str] = None
    trackable: TrackableCriteria = TrackableCriteria()
    page: PageRequest = PageRequest()
```

- `actor` is optional on `Query`; the bus fills in the current actor.
- Paginated queries take a `PageRequest` and return `Page[T]`, whose `pages` / `has_prev` /
  `prev_num` / `has_next` / `next_num` match Flask-SQLAlchemy's `Pagination`.
- Export it in [`project/application/queries/__init__.py`](../../project/application/queries/__init__.py).

### 3. Abstract read repository

Location: `project/application/read_repositories/abstract_<entity>_read_repository.py`

```python
import abc


class AbstractEventOrganizerReadRepository(abc.ABC):
    @abc.abstractmethod
    def list(
        self, query: ListEventOrganizersQuery
    ) -> Page[EventOrganizerListItemReadModel]:  # pragma: no cover
        raise NotImplementedError
```

Pass the query object itself to list methods, so filters are not duplicated in signatures.

### 4. SQLAlchemy read repository

Location: `project/infrastructure/read_repositories/sql_alchemy_<entity>_read_repository.py`

- Take `session` in the constructor; it is the **read-only** session.
- Use `select()`, load relationships explicitly (`joinedload`, `selectinload`, `undefer`),
  count with `select(func.count()).select_from(<filtered select>.subquery())`.
- Map rows to read models in module-private functions (`_to_list_item(...)`) **before
  returning**. Do not add `to_read_model` methods to ORM models.
- Add a deterministic tiebreak (`id`) to every paginated ordering.
- Reuse [`query_helpers.py`](../../project/infrastructure/read_repositories/query_helpers.py):
  `trackable_filters(model, criteria)`, `count(...)` and `paginate(session, stmt,
  count_stmt, page_request, to_item)`.
- Deferred column groups (`detail`, `trackable`) must be undeferred explicitly
  (`undefer_group(...)`), or the mapping triggers lazy loads on the read session.
- Reference: [`sql_alchemy_event_organizer_read_repository.py`](../../project/infrastructure/read_repositories/sql_alchemy_event_organizer_read_repository.py).

### 5. Handler

Location: `project/application/query_handlers/<snake_case_name>_handler.py` (one handler
per file, as in `command_handlers/`)

```python
from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)


class ListEventOrganizersHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventOrganizerReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventOrganizersQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        return self.repo.list(query)
```

- Repositories come in through the constructor; `handle` gets no unit of work.
- Keep handlers thin. Authorize private data against `query.actor` here (see "Authorization" below).
- Export it in [`project/application/query_handlers/__init__.py`](../../project/application/query_handlers/__init__.py).

### 5a. Authorization

Handlers for private data enforce the permission themselves, the same rule commands use
(`actor_permission_policy`, platform admin → member role → app installation grant), so the
data is protected whatever the caller (view, API, Celery, a nested query).

```python
class ListOrganizationInvitationsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractOrganizationInvitationReadRepository,
                 authz: ActorAuthorizationService):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListOrganizationInvitationsQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None  # not found before permission, as in commands

        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, "organization_invitations:read"
        )
        return self.repo.list(query)
```

- Inject `ActorAuthorizationService` as `authz` (`Cqrs.actor_authorization_service`).
- Return `None` for not-found **before** `ensure_permission_for_admin_unit`.
- Detail queries load first and authorize on the loaded `admin_unit_id`.
- A missing actor fails closed with `UnauthorizedError` (API: JSON 401; views: 401 via the
  app-level error handler).
- The OAuth scope check stays a delivery concern. Delivery decorators
  (`require_organization_api_access`, `manage_permission_required`) stay until S10; the
  handler check is the second line.
- Reference implementation: organization invitations.

### 6. Wire up the container

In [`project/container.py`](../../project/container.py):

```python
class ReadRepos(containers.DeclarativeContainer):
    event_organizer_read_repo = providers.Factory(
        SqlAlchemyEventOrganizerReadRepository,
        session=infrastructure.read_session,  # not session_factory
    )

class Cqrs(containers.DeclarativeContainer):
    query_handler_factory = providers.Singleton(
        QueryHandlerFactory,
        factory_aggregate=providers.FactoryAggregate(
            {
                queries.ListEventOrganizersQuery: providers.Factory(
                    query_handlers.ListEventOrganizersHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
            }
        ),
    )
```

### 7. Call it from delivery code

**API resource** (`BaseResource` has `self.query_bus`). Build paging and trackable
criteria from the webargs kwargs with [`project/api/query_args.py`](../../project/api/query_args.py):
```python
from project.api.query_args import page_request_from_kwargs, trackable_criteria_from_kwargs
from project.views.utils import abort_if_page_out_of_range, result_or_404

query = ListEventOrganizersQuery(
    admin_unit_id=id,
    name=kwargs.get("name"),
    sort=kwargs.get("sort"),
    trackable=trackable_criteria_from_kwargs(kwargs),
    page=page_request_from_kwargs(kwargs),
)
page = result_or_404(self.query_bus.handle(query))
abort_if_page_out_of_range(page)
return page
```
The existing `SQLAlchemySchema` dump schemas render read models unchanged (attribute
access only).

**Modular list view**: override `create_list_query` on the view handler. The list
view always runs the returned query through the bus.
Use `KeySortDefinition` / `KeySearchDefinition` (column-free) for the sort and keyword
fields, and map `form.sort.data` / `form.keyword.data` onto the query.
Map unknown sort keys to `None` (the ORM path ignored them; a strict enum would 500).
Display props for computed fields use `keypath` (`BoolProp(..., keypath="has_logo")`).
```python
def create_list_query(self, form, page_request, **kwargs):
    return ListEventOrganizersQuery(
        admin_unit_id=current_admin_unit.id,
        keyword=form.keyword.data or None,
        sort=_sort_or_none(form.sort.data),
        page=page_request,
    )
```

**Modular update/delete/read views**: override `create_get_query(object_id)` on the view
handler. `get_object_by_id` loads the object through the query bus. The result is passed to the form as `obj=`,
so the read model's attribute names must equal the form field names (WTForms reads them by
name; a missing attribute silently leaves the field empty). Use a use-case shaped
`<Entity>EditReadModel`. Images use `ImageEditReadModel` (needs `undefer(Image.data)`), and
the model must expose `admin_unit_id` for `check_object_access`. Once the list **and** the
object are query-backed, drop `model` / `object_service` and set the plain metadata
attributes instead (copy the values from the `*_generated.py` model: they drive URLs,
endpoints, permissions and titles). Override `get_object_title(object)` because `str()`
on a read model is not the ORM `__str__`.
```python
model_name = "event_organizer"
model_name_plural = "event_organizers"
display_name = "Event organizer"          # msgid, translated at call time
display_name_plural = "Event organizers"

def create_get_query(self, object_id):
    return GetEventOrganizerForEditQuery(id=object_id)

def get_object_title(self, object):
    return object.name
```

**Modular forms** (e.g. `ajax_validate_<field>`): `self.get_query_bus().handle(query)`.

**Flat view functions** (`project/views/*.py`): inject the bus like the message bus.
```python
from dependency_injector.wiring import Provide, inject

@inject
def organizer_list(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    page_request = page_request_from_request_args()
    ...
```

### 8. Ratchet the import-linter contract

If the delivery module no longer imports `project.models`, its `ignore_imports` line in
the `delivery-reads-through-queries` contract of [`.importlinter`](../../.importlinter)
is now unmatched and `lint-imports` fails. Regenerate the list:

```bash
python .scripts/models_import_ignores.py --write
python .scripts/read_path_report.py   # paste before/after into the PR
```

Never add an entry by hand: new delivery code reads through queries.

### 9. Tests

- **Handler** (no DB): `tests/application/query_handlers/test_<entity>_query_handlers.py`
  with a fake read repository.
- **Read repository** (DB): `tests/infrastructure/read_repositories/test_sql_alchemy_<entity>_read_repository.py`.
  Seed with `seeder`, resolve the repo inside `app.app_context()` from
  `app.container.read_repos`, and wrap calls in `app.container.infrastructure.read_session_scope()`.
- **Delivery**: the existing view / API tests must pass unchanged; add parity cases
  (404s, sort keys, out-of-range pages).
- **API parity snapshot**: before switching an endpoint, capture its responses with fixed
  seed data and timestamps, then assert byte equality after the switch. Example:
  [`tests/api/test_organizer_read_parity.py`](../../tests/api/test_organizer_read_parity.py).

## Pitfalls

- **Return materialized read models.** The read session is removed when the bus returns;
  any lazy load on an ORM object after that fails. This is intentional: it turns hidden
  N+1 loads into loud errors.
- **The read session sees only committed data.** Commands commit inside
  `MessageBus.handle`, so querying after a command is fine. Never query
  between `db.session.add(...)` and the commit.
- Event-handler read repos (`event_read_repo`, `webhook_delivery_read_repo`) run inside a
  unit of work and stay on `session_factory`. Only query-side repos use `read_session`.

## References

- Bus: [`project/application/query_bus.py`](../../project/application/query_bus.py)
- Read session + scope: [`project/infrastructure/read_session.py`](../../project/infrastructure/read_session.py)
- Pagination: [`project/application/read_models/page.py`](../../project/application/read_models/page.py),
  [`project/views/utils.py`](../../project/views/utils.py) (`page_request_from_request_args`,
  `abort_if_page_out_of_range`, `result_or_404`)
- Migration plan: `.agents/plans/2026-10-13-cqrs-read-side-migration.plan.md`
