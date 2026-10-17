"""Organization member query handlers — fake repository and reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOrganizationMemberHandler,
    GetUserOrganizationMembershipHandler,
    ListOrganizationMemberRolesHandler,
    ListOrganizationMembersHandler,
    ListUserOrganizationMembershipsHandler,
)
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
    OrganizationMemberRoleReadModel,
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_models.user_ref_read_model import UserRefReadModel
from project.application.read_repositories.abstract_organization_member_read_repository import (
    AbstractOrganizationMemberReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

PERMISSION = "organization_members:read"


def _member(member_id, admin_unit_id=7):
    return OrganizationMemberReadModel(
        id=member_id,
        admin_unit_id=admin_unit_id,
        user_id=9,
        user=UserRefReadModel(id=9, email="member@test.de"),
    )


def _membership(member_id, user_id=7):
    return UserOrganizationMembershipReadModel(
        id=member_id,
        admin_unit_id=3,
        user_id=user_id,
        admin_unit=OrganizationRefReadModel(id=3, name="Crew"),
    )


class FakeRepo(AbstractOrganizationMemberReadRepository):
    def __init__(self, organization_ids=(), members=(), memberships=()):
        self.organization_ids = set(organization_ids)
        self.members = {member.id: member for member in members}
        self.memberships = {membership.id: membership for membership in memberships}
        self.queries = []

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def _page(self, query, items):
        self.queries.append(query)
        return Page(items=items, page=1, per_page=20, total=len(items))

    def list(self, query):
        return self._page(query, list(self.members.values()))

    def get(self, object_id):
        return self.members.get(object_id)

    def list_for_user(self, query):
        return self._page(query, list(self.memberships.values()))

    def get_membership(self, object_id):
        return self.memberships.get(object_id)

    def list_roles(self):
        return [OrganizationMemberRoleReadModel(id=1, name="admin", title="Admin")]


class TestListOrganizationMembersHandler:
    def test_unknown_organization_returns_none(self):
        handler = ListOrganizationMembersHandler(FakeRepo(), authz())

        query = queries.ListOrganizationMembersQuery(admin_unit_id=7, actor=ACTOR)

        assert handler.handle(query) is None

    def test_refused_actor_raises(self):
        repo = FakeRepo(organization_ids=[7])
        handler = ListOrganizationMembersHandler(repo, authz())

        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.ListOrganizationMembersQuery(admin_unit_id=7, actor=ACTOR)
            )

        assert repo.queries == []

    def test_permitted_actor_gets_the_page(self):
        repo = FakeRepo(organization_ids=[7], members=[_member(1)])
        spy = authz(PERMISSION)

        page = ListOrganizationMembersHandler(repo, spy).handle(
            queries.ListOrganizationMembersQuery(admin_unit_id=7, actor=ACTOR)
        )

        assert [item.id for item in page.items] == [1]
        assert spy.ensured == [(ACTOR, 7, PERMISSION)]


class TestGetOrganizationMemberHandler:
    def test_unknown_returns_none(self):
        handler = GetOrganizationMemberHandler(FakeRepo(), authz())

        assert (
            handler.handle(queries.GetOrganizationMemberQuery(id=1, actor=ACTOR))
            is None
        )

    def test_member_of_other_organization_is_refused(self):
        handler = GetOrganizationMemberHandler(
            FakeRepo(members=[_member(1, admin_unit_id=8)]), authz(PERMISSION)
        )

        with pytest.raises(UnauthorizedError):
            handler.handle(queries.GetOrganizationMemberQuery(id=1, actor=ACTOR))

    def test_permitted_actor_gets_the_member(self):
        member = _member(1)
        handler = GetOrganizationMemberHandler(
            FakeRepo(members=[member]), authz(PERMISSION)
        )

        assert (
            handler.handle(queries.GetOrganizationMemberQuery(id=1, actor=ACTOR))
            == member
        )


class TestUserMemberships:
    def test_list_requires_the_user(self):
        handler = ListUserOrganizationMembershipsHandler(FakeRepo(), authz())

        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.ListUserOrganizationMembershipsQuery(user_id=8, actor=ACTOR)
            )

    def test_list_for_the_user(self):
        repo = FakeRepo(memberships=[_membership(1)])
        handler = ListUserOrganizationMembershipsHandler(repo, authz())

        page = handler.handle(
            queries.ListUserOrganizationMembershipsQuery(user_id=7, actor=ACTOR)
        )

        assert [item.id for item in page.items] == [1]

    def test_get_unknown_returns_none(self):
        handler = GetUserOrganizationMembershipHandler(FakeRepo(), authz())

        assert (
            handler.handle(
                queries.GetUserOrganizationMembershipQuery(id=1, actor=ACTOR)
            )
            is None
        )

    def test_get_membership_of_other_user_is_refused(self):
        handler = GetUserOrganizationMembershipHandler(
            FakeRepo(memberships=[_membership(1, user_id=8)]), authz()
        )

        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.GetUserOrganizationMembershipQuery(id=1, actor=ACTOR)
            )

    def test_get_own_membership(self):
        membership = _membership(1)
        handler = GetUserOrganizationMembershipHandler(
            FakeRepo(memberships=[membership]), authz()
        )

        assert (
            handler.handle(
                queries.GetUserOrganizationMembershipQuery(id=1, actor=ACTOR)
            )
            == membership
        )


def test_roles_are_listed_without_authorization():
    roles = ListOrganizationMemberRolesHandler(FakeRepo()).handle(
        queries.ListOrganizationMemberRolesQuery()
    )

    assert [role.name for role in roles] == ["admin"]
