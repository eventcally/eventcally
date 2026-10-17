"""Event reference query handlers — fake repository, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetIncomingEventReferenceHandler,
    ListIncomingEventReferencesHandler,
    ListOutgoingEventReferencesHandler,
)
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.event_reference_read_models import (
    EventReferenceReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_reference_read_repository import (
    AbstractEventReferenceReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

CREW = OrganizationRefReadModel(id=8, name="Crew")


def _reference(reference_id, admin_unit_id=7):
    return EventReferenceReadModel(
        id=reference_id,
        admin_unit_id=admin_unit_id,
        event_id=1,
        event=EventRefReadModel(id=1, name="Event", admin_unit=CREW),
        admin_unit=OrganizationRefReadModel(id=admin_unit_id, name="Mine"),
    )


class FakeRepo(AbstractEventReferenceReadRepository):
    def __init__(self, references=()):
        self.references = {r.id: r for r in references}

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def _page(self):
        items = list(self.references.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def list_incoming(self, query):
        return self._page()

    def list_outgoing(self, query):
        return self._page()

    def get(self, object_id):
        return self.references.get(object_id)


def test_ref_models_render_as_names():
    assert str(CREW) == "Crew"
    assert str(_reference(1).event) == "Event"


@pytest.mark.parametrize(
    "handler_class, query_class, permission",
    [
        (
            ListIncomingEventReferencesHandler,
            queries.ListIncomingEventReferencesQuery,
            "incoming_event_references:read",
        ),
        (
            ListOutgoingEventReferencesHandler,
            queries.ListOutgoingEventReferencesQuery,
            "outgoing_event_references:read",
        ),
    ],
)
def test_lists(handler_class, query_class, permission):
    repo = FakeRepo([_reference(1)])

    assert (
        handler_class(repo, authz(permission))
        .handle(query_class(admin_unit_id=7, actor=ACTOR))
        .total
        == 1
    )
    assert (
        handler_class(repo, authz(permission)).handle(
            query_class(admin_unit_id=9, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler_class(repo, authz()).handle(query_class(admin_unit_id=7, actor=ACTOR))


def test_get():
    handler = GetIncomingEventReferenceHandler(
        FakeRepo([_reference(1), _reference(2, admin_unit_id=9)]),
        authz("incoming_event_references:read"),
    )

    assert handler.handle(
        queries.GetIncomingEventReferenceQuery(id=1, actor=ACTOR)
    ) == _reference(1)
    assert (
        handler.handle(queries.GetIncomingEventReferenceQuery(id=3, actor=ACTOR))
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetIncomingEventReferenceQuery(id=2, actor=ACTOR))


def test_get_reference_is_public():
    from project.application.query_handlers import GetEventReferenceHandler

    handler = GetEventReferenceHandler(FakeRepo([_reference(1, admin_unit_id=9)]))

    assert handler.handle(queries.GetEventReferenceQuery(id=1)).id == 1
    assert handler.handle(queries.GetEventReferenceQuery(id=2)) is None
