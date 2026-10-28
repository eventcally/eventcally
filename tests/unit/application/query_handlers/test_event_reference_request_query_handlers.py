"""Event reference request query handlers — fake repository, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOutgoingEventReferenceRequestHandler,
    ListIncomingEventReferenceRequestsHandler,
    ListOutgoingEventReferenceRequestsHandler,
)
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_event_reference_request_read_repository import (
    AbstractEventReferenceRequestReadRepository,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz


def _request(request_id, event_admin_unit_id=7):
    return EventReferenceRequestReadModel(
        id=request_id,
        admin_unit_id=9,
        event_id=1,
        review_status=EventReferenceRequestReviewStatus.inbox,
        event=EventRefReadModel(
            id=1,
            name="Event",
            admin_unit=OrganizationRefReadModel(id=event_admin_unit_id, name="Mine"),
        ),
        admin_unit=OrganizationRefReadModel(id=9, name="Other"),
    )


class FakeRepo(AbstractEventReferenceRequestReadRepository):
    def __init__(self, requests=()):
        self.requests = {r.id: r for r in requests}
        self.queries = []

    def auto_verifies(self, source, target):  # pragma: no cover
        return False

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def _page(self, query):
        self.queries.append(query)
        items = list(self.requests.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def list_incoming(self, query):
        return self._page(query)

    def list_outgoing(self, query):
        return self._page(query)

    def get(self, object_id):
        return self.requests.get(object_id)


@pytest.mark.parametrize(
    "handler_class, query_class, permission",
    [
        (
            ListIncomingEventReferenceRequestsHandler,
            queries.ListIncomingEventReferenceRequestsQuery,
            "incoming_event_reference_requests:read",
        ),
        (
            ListOutgoingEventReferenceRequestsHandler,
            queries.ListOutgoingEventReferenceRequestsQuery,
            "outgoing_event_reference_requests:read",
        ),
    ],
)
def test_lists(handler_class, query_class, permission):
    repo = FakeRepo([_request(1)])
    query = query_class(
        admin_unit_id=7,
        review_status=EventReferenceRequestReviewStatus.rejected,
        actor=ACTOR,
    )

    assert handler_class(repo, authz(permission)).handle(query).total == 1
    assert repo.queries == [query]
    assert (
        handler_class(repo, authz(permission)).handle(
            query_class(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler_class(repo, authz()).handle(query_class(admin_unit_id=7, actor=ACTOR))


def test_get_outgoing_authorizes_on_the_event_organization():
    handler = GetOutgoingEventReferenceRequestHandler(
        FakeRepo([_request(1), _request(2, event_admin_unit_id=8)]),
        authz("outgoing_event_reference_requests:read"),
    )

    assert (
        handler.handle(
            queries.GetOutgoingEventReferenceRequestQuery(id=1, actor=ACTOR)
        ).id
        == 1
    )
    assert (
        handler.handle(queries.GetOutgoingEventReferenceRequestQuery(id=3, actor=ACTOR))
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetOutgoingEventReferenceRequestQuery(id=2, actor=ACTOR))


def test_get_incoming_authorizes_on_the_requested_organization():
    from project.application.query_handlers import (
        GetIncomingEventReferenceRequestHandler,
    )

    permission = "incoming_event_reference_requests:read"
    repo = FakeRepo([_request(1)])

    def query(request_id):
        return queries.GetIncomingEventReferenceRequestQuery(id=request_id, actor=ACTOR)

    handler = GetIncomingEventReferenceRequestHandler(
        repo, authz(permission, admin_unit_id=9)
    )
    assert handler.handle(query(1)).id == 1
    assert handler.handle(query(3)) is None
    # The event owner (admin unit 7) is on the other side.
    with pytest.raises(UnauthorizedError):
        GetIncomingEventReferenceRequestHandler(repo, authz(permission)).handle(
            query(1)
        )
