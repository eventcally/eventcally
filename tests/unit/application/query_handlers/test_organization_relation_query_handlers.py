"""Organization relation query handlers — fake repository."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOutgoingOrganizationRelationHandler,
    ListOutgoingOrganizationRelationsHandler,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_relation_read_repository import (
    AbstractOrganizationRelationReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

PERMISSION = "outgoing_organization_relations:read"


def _relation(relation_id, source_admin_unit_id=7):
    return OrganizationRelationReadModel(
        id=relation_id,
        source_admin_unit_id=source_admin_unit_id,
        target_admin_unit_id=9,
        source_admin_unit=OrganizationRefReadModel(id=source_admin_unit_id, name="S"),
        target_admin_unit=OrganizationRefReadModel(id=9, name="T"),
    )


class FakeRepo(AbstractOrganizationRelationReadRepository):
    def __init__(self, relations=()):
        self.relations = {r.id: r for r in relations}
        self.queries = []

    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def list(self, query):
        self.queries.append(query)
        items = list(self.relations.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get(self, object_id):
        return self.relations.get(object_id)

    def get_by_target(self, admin_unit_id, target_admin_unit_id):
        return next(
            (
                r
                for r in self.relations.values()
                if r.source_admin_unit_id == admin_unit_id
                and r.target_admin_unit_id == target_admin_unit_id
            ),
            None,
        )


def test_list():
    repo = FakeRepo([_relation(1)])
    query = queries.ListOutgoingOrganizationRelationsQuery(
        admin_unit_id=7, keyword="crew", verify=True, actor=ACTOR
    )

    assert (
        ListOutgoingOrganizationRelationsHandler(repo, authz(PERMISSION))
        .handle(query)
        .total
        == 1
    )
    assert repo.queries == [query]
    assert (
        ListOutgoingOrganizationRelationsHandler(repo, authz(PERMISSION)).handle(
            queries.ListOutgoingOrganizationRelationsQuery(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        ListOutgoingOrganizationRelationsHandler(repo, authz()).handle(query)


def test_get():
    handler = GetOutgoingOrganizationRelationHandler(
        FakeRepo([_relation(1), _relation(2, source_admin_unit_id=8)]),
        authz(PERMISSION),
    )

    assert (
        handler.handle(
            queries.GetOutgoingOrganizationRelationQuery(id=1, actor=ACTOR)
        ).id
        == 1
    )
    assert (
        handler.handle(queries.GetOutgoingOrganizationRelationQuery(id=3, actor=ACTOR))
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(queries.GetOutgoingOrganizationRelationQuery(id=2, actor=ACTOR))


def test_get_by_target():
    from project.application.query_handlers import (
        GetOutgoingOrganizationRelationByTargetHandler,
    )

    handler = GetOutgoingOrganizationRelationByTargetHandler(
        FakeRepo([_relation(1), _relation(2, source_admin_unit_id=8)]),
        authz(PERMISSION),
    )

    assert (
        handler.handle(
            queries.GetOutgoingOrganizationRelationByTargetQuery(
                admin_unit_id=7, target_admin_unit_id=9, actor=ACTOR
            )
        ).id
        == 1
    )
    assert (
        handler.handle(
            queries.GetOutgoingOrganizationRelationByTargetQuery(
                admin_unit_id=7, target_admin_unit_id=10, actor=ACTOR
            )
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        handler.handle(
            queries.GetOutgoingOrganizationRelationByTargetQuery(
                admin_unit_id=8, target_admin_unit_id=9, actor=ACTOR
            )
        )
