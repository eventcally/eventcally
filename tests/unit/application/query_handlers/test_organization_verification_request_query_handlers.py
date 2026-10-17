"""Organization verification request query handlers — fake repository."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOutgoingOrganizationVerificationRequestHandler,
    ListIncomingOrganizationVerificationRequestsHandler,
    ListOutgoingOrganizationVerificationRequestsHandler,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_verification_request_read_repository import (
    AbstractOrganizationVerificationRequestReadRepository,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz


def _request(request_id, source_admin_unit_id=7):
    return OrganizationVerificationRequestReadModel(
        id=request_id,
        source_admin_unit_id=source_admin_unit_id,
        target_admin_unit_id=9,
        review_status=OrganizationVerificationRequestReviewStatus.inbox,
        source_admin_unit=OrganizationRefReadModel(id=source_admin_unit_id, name="S"),
        target_admin_unit=OrganizationRefReadModel(id=9, name="T"),
    )


class FakeRepo(AbstractOrganizationVerificationRequestReadRepository):
    def __init__(self, requests=()):
        self.requests = {r.id: r for r in requests}

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def _page(self):
        items = list(self.requests.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def list_incoming(self, query):
        return self._page()

    def list_outgoing(self, query):
        return self._page()

    def get(self, object_id):
        return self.requests.get(object_id)

    def get_review(self, object_id):
        return None


@pytest.mark.parametrize(
    "handler_class, query_class, permission",
    [
        (
            ListIncomingOrganizationVerificationRequestsHandler,
            queries.ListIncomingOrganizationVerificationRequestsQuery,
            "incoming_organization_verification_requests:read",
        ),
        (
            ListOutgoingOrganizationVerificationRequestsHandler,
            queries.ListOutgoingOrganizationVerificationRequestsQuery,
            "outgoing_organization_verification_requests:read",
        ),
    ],
)
def test_lists(handler_class, query_class, permission):
    repo = FakeRepo([_request(1)])

    assert (
        handler_class(repo, authz(permission))
        .handle(query_class(admin_unit_id=7, actor=ACTOR))
        .total
        == 1
    )
    assert (
        handler_class(repo, authz(permission)).handle(
            query_class(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler_class(repo, authz()).handle(query_class(admin_unit_id=7, actor=ACTOR))


def test_get_outgoing():
    handler = GetOutgoingOrganizationVerificationRequestHandler(
        FakeRepo([_request(1), _request(2, source_admin_unit_id=8)]),
        authz("outgoing_organization_verification_requests:read"),
    )

    assert (
        handler.handle(
            queries.GetOutgoingOrganizationVerificationRequestQuery(id=1, actor=ACTOR)
        ).id
        == 1
    )
    assert (
        handler.handle(
            queries.GetOutgoingOrganizationVerificationRequestQuery(id=3, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(
            queries.GetOutgoingOrganizationVerificationRequestQuery(id=2, actor=ACTOR)
        )
