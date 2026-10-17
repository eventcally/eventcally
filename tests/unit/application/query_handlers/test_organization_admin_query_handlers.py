"""Admin area organization query handlers — fake repository."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOrganizationForAdminHandler,
    ListOrganizationsForAdminHandler,
)
from project.application.read_models.organization_admin_read_models import (
    OrganizationAdminReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_admin_read_repository import (
    AbstractOrganizationAdminReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

ORG = OrganizationAdminReadModel(id=1, name="Crew")


class FakeRepo(AbstractOrganizationAdminReadRepository):
    def list(self, query):
        return Page(items=[ORG], page=1, per_page=20, total=1)

    def get(self, object_id):
        return ORG if object_id == 1 else None


def test_platform_admin_only():
    admin = authz(admins=[7])

    assert (
        ListOrganizationsForAdminHandler(FakeRepo(), admin)
        .handle(queries.ListOrganizationsForAdminQuery(actor=ACTOR))
        .total
        == 1
    )
    assert (
        GetOrganizationForAdminHandler(FakeRepo(), admin).handle(
            queries.GetOrganizationForAdminQuery(id=1, actor=ACTOR)
        )
        == ORG
    )
    assert (
        GetOrganizationForAdminHandler(FakeRepo(), admin).handle(
            queries.GetOrganizationForAdminQuery(id=2, actor=ACTOR)
        )
        is None
    )

    with pytest.raises(UnauthorizedError):
        ListOrganizationsForAdminHandler(FakeRepo(), authz()).handle(
            queries.ListOrganizationsForAdminQuery(actor=ACTOR)
        )
    with pytest.raises(UnauthorizedError):
        GetOrganizationForAdminHandler(FakeRepo(), authz()).handle(
            queries.GetOrganizationForAdminQuery(id=1, actor=ACTOR)
        )
