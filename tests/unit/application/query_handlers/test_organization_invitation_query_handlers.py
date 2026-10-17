"""Organization invitation query handlers — fake repository and reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetOrganizationInvitationHandler,
    ListOrganizationInvitationsHandler,
)
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
    OrganizationInvitationListItemReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_invitation_read_repository import (
    AbstractOrganizationInvitationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_actor_permission_policy import (
    FakeActorPermissionReader,
)

PERMISSION = "organization_invitations:read"
ACTOR = Actor(user_id=7)


class FakeOrganizationInvitationReadRepository(
    AbstractOrganizationInvitationReadRepository
):
    def __init__(self, organization_ids=(), details=()):
        self.organization_ids = set(organization_ids)
        self.details = {detail.id: detail for detail in details}
        self.list_queries = []

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def list(self, query):
        self.list_queries.append(query)
        return Page[OrganizationInvitationListItemReadModel](
            items=[
                OrganizationInvitationListItemReadModel(id=1, email="invited@test.de")
            ],
            page=query.page.page,
            per_page=query.page.per_page,
            total=1,
        )

    def get(self, object_id):
        return self.details.get(object_id)

    def list_for_user(self, query):
        self.list_queries.append(query)
        items = list(self.details.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def get_recipient_email(self, object_id):
        detail = self.details.get(object_id)
        return detail.email if detail else None


class SpyAuthorizationService(ActorAuthorizationService):
    def __init__(self, reader):
        super().__init__(reader)
        self.ensured = []

    def ensure_permission_for_admin_unit(self, actor, admin_unit_id, permission):
        self.ensured.append((actor, admin_unit_id, permission))
        super().ensure_permission_for_admin_unit(actor, admin_unit_id, permission)


def _detail(invitation_id, admin_unit_id):
    return OrganizationInvitationDetailReadModel(
        id=invitation_id,
        email="invited@test.de",
        admin_unit_id=admin_unit_id,
        admin_unit=OrganizationRefReadModel(id=admin_unit_id, name="Crew"),
    )


def _authz(permitted=True):
    members = [(7, 7, PERMISSION)] if permitted else []
    return SpyAuthorizationService(FakeActorPermissionReader(members=members))


class TestListOrganizationInvitationsHandler:
    def test_unknown_organization_returns_none_without_authorizing(self):
        authz = _authz()
        handler = ListOrganizationInvitationsHandler(
            FakeOrganizationInvitationReadRepository(), authz
        )

        query = queries.ListOrganizationInvitationsQuery(admin_unit_id=7, actor=ACTOR)

        assert handler.handle(query) is None
        assert authz.ensured == []

    def test_refused_actor_raises_and_does_not_list(self):
        repo = FakeOrganizationInvitationReadRepository(organization_ids=[7])
        handler = ListOrganizationInvitationsHandler(repo, _authz(permitted=False))

        query = queries.ListOrganizationInvitationsQuery(admin_unit_id=7, actor=ACTOR)

        with pytest.raises(UnauthorizedError):
            handler.handle(query)

        assert repo.list_queries == []

    def test_missing_actor_is_refused(self):
        repo = FakeOrganizationInvitationReadRepository(organization_ids=[7])
        handler = ListOrganizationInvitationsHandler(repo, _authz())

        with pytest.raises(UnauthorizedError):
            handler.handle(queries.ListOrganizationInvitationsQuery(admin_unit_id=7))

    def test_permitted_actor_gets_the_page(self):
        repo = FakeOrganizationInvitationReadRepository(organization_ids=[7])
        authz = _authz()
        handler = ListOrganizationInvitationsHandler(repo, authz)

        query = queries.ListOrganizationInvitationsQuery(admin_unit_id=7, actor=ACTOR)
        page = handler.handle(query)

        assert [item.email for item in page.items] == ["invited@test.de"]
        assert authz.ensured == [(ACTOR, 7, PERMISSION)]
        assert repo.list_queries == [query]


class TestGetOrganizationInvitationHandler:
    def test_unknown_id_returns_none_not_unauthorized(self):
        handler = GetOrganizationInvitationHandler(
            FakeOrganizationInvitationReadRepository(), _authz(permitted=False)
        )

        query = queries.GetOrganizationInvitationQuery(id=1, actor=ACTOR)

        assert handler.handle(query) is None

    def test_invitation_of_another_organization_is_refused(self):
        repo = FakeOrganizationInvitationReadRepository(details=[_detail(1, 8)])
        handler = GetOrganizationInvitationHandler(repo, _authz())

        with pytest.raises(UnauthorizedError):
            handler.handle(queries.GetOrganizationInvitationQuery(id=1, actor=ACTOR))

    def test_permitted_actor_gets_the_detail_authorized_on_its_organization(self):
        detail = _detail(1, 7)
        authz = _authz()
        handler = GetOrganizationInvitationHandler(
            FakeOrganizationInvitationReadRepository(details=[detail]), authz
        )

        result = handler.handle(
            queries.GetOrganizationInvitationQuery(id=1, actor=ACTOR)
        )

        assert result == detail
        assert authz.ensured == [(ACTOR, 7, PERMISSION)]


class TestUserSideOrganizationInvitations:
    def _authz(self):
        return ActorAuthorizationService(
            FakeActorPermissionReader(emails={7: "Invited@Test.de"})
        )

    def test_list_requires_the_user(self):
        from project.application.query_handlers import (
            ListUserOrganizationInvitationsHandler,
        )

        handler = ListUserOrganizationInvitationsHandler(
            FakeOrganizationInvitationReadRepository(details=[_detail(1, 3)]),
            self._authz(),
        )

        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.ListUserOrganizationInvitationsQuery(user_id=8, actor=ACTOR)
            )

        page = handler.handle(
            queries.ListUserOrganizationInvitationsQuery(user_id=7, actor=ACTOR)
        )
        assert [item.id for item in page.items] == [1]

    def test_get_for_recipient_only(self):
        from project.application.query_handlers import (
            GetUserOrganizationInvitationHandler,
        )

        other = _detail(2, 3).model_copy(update={"email": "other@test.de"})
        handler = GetUserOrganizationInvitationHandler(
            FakeOrganizationInvitationReadRepository(details=[_detail(1, 3), other]),
            self._authz(),
        )

        assert handler.handle(
            queries.GetUserOrganizationInvitationQuery(id=1, actor=ACTOR)
        ) == _detail(1, 3)
        assert (
            handler.handle(
                queries.GetUserOrganizationInvitationQuery(id=3, actor=ACTOR)
            )
            is None
        )
        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.GetUserOrganizationInvitationQuery(id=2, actor=ACTOR)
            )

    def test_recipient_email_is_public(self):
        from project.application.query_handlers import (
            GetOrganizationInvitationRecipientHandler,
        )

        handler = GetOrganizationInvitationRecipientHandler(
            FakeOrganizationInvitationReadRepository(details=[_detail(1, 3)])
        )

        assert (
            handler.handle(queries.GetOrganizationInvitationRecipientQuery(id=1))
            == "invited@test.de"
        )
        assert (
            handler.handle(queries.GetOrganizationInvitationRecipientQuery(id=2))
            is None
        )
