"""Member invitation query handlers — fake repository and reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetMemberInvitationRecipientHandler,
    GetOrganizationMemberInvitationHandler,
    GetUserMemberInvitationHandler,
    ListOrganizationMemberInvitationsHandler,
    ListUserMemberInvitationsHandler,
)
from project.application.read_models.organization_member_invitation_read_models import (
    OrganizationMemberInvitationReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_member_invitation_read_repository import (
    AbstractOrganizationMemberInvitationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz
from tests.unit.application.services.test_actor_permission_policy import (
    FakeActorPermissionReader,
)

PERMISSION = "organization_member_invitations:read"


def _invitation(invitation_id, admin_unit_id=7, email="invited@test.de"):
    return OrganizationMemberInvitationReadModel(
        id=invitation_id,
        admin_unit_id=admin_unit_id,
        email=email,
        roles="admin",
        admin_unit=OrganizationRefReadModel(id=admin_unit_id, name="Crew"),
    )


class FakeRepo(AbstractOrganizationMemberInvitationReadRepository):
    def __init__(self, organization_ids=(), invitations=()):
        self.organization_ids = set(organization_ids)
        self.invitations = {i.id: i for i in invitations}
        self.queries = []

    def organization_exists(self, admin_unit_id):
        return admin_unit_id in self.organization_ids

    def _page(self, query):
        self.queries.append(query)
        items = list(self.invitations.values())
        return Page(items=items, page=1, per_page=20, total=len(items))

    def list(self, query):
        return self._page(query)

    def get(self, object_id):
        return self.invitations.get(object_id)

    def list_for_user(self, query):
        return self._page(query)

    def get_recipient_email(self, object_id):
        invitation = self.invitations.get(object_id)
        return invitation.email if invitation else None


def _recipient_authz():
    return ActorAuthorizationService(
        FakeActorPermissionReader(emails={7: "Invited@test.de"})
    )


class TestOrganizationSide:
    def test_list_unknown_organization_returns_none(self):
        handler = ListOrganizationMemberInvitationsHandler(FakeRepo(), authz())

        assert (
            handler.handle(
                queries.ListOrganizationMemberInvitationsQuery(
                    admin_unit_id=7, actor=ACTOR
                )
            )
            is None
        )

    def test_list_requires_permission(self):
        repo = FakeRepo(organization_ids=[7])

        with pytest.raises(UnauthorizedError):
            ListOrganizationMemberInvitationsHandler(repo, authz()).handle(
                queries.ListOrganizationMemberInvitationsQuery(
                    admin_unit_id=7, actor=ACTOR
                )
            )

        assert repo.queries == []

    def test_list_permitted(self):
        repo = FakeRepo(organization_ids=[7], invitations=[_invitation(1)])

        page = ListOrganizationMemberInvitationsHandler(repo, authz(PERMISSION)).handle(
            queries.ListOrganizationMemberInvitationsQuery(admin_unit_id=7, actor=ACTOR)
        )

        assert [item.id for item in page.items] == [1]

    def test_get(self):
        handler = GetOrganizationMemberInvitationHandler(
            FakeRepo(invitations=[_invitation(1), _invitation(2, admin_unit_id=8)]),
            authz(PERMISSION),
        )

        assert handler.handle(
            queries.GetOrganizationMemberInvitationQuery(id=1, actor=ACTOR)
        ) == _invitation(1)
        assert (
            handler.handle(
                queries.GetOrganizationMemberInvitationQuery(id=3, actor=ACTOR)
            )
            is None
        )
        with pytest.raises(UnauthorizedError):
            handler.handle(
                queries.GetOrganizationMemberInvitationQuery(id=2, actor=ACTOR)
            )


class TestUserSide:
    def test_list_requires_the_user(self):
        with pytest.raises(UnauthorizedError):
            ListUserMemberInvitationsHandler(FakeRepo(), authz()).handle(
                queries.ListUserMemberInvitationsQuery(user_id=8, actor=ACTOR)
            )

    def test_list_for_the_user(self):
        repo = FakeRepo(invitations=[_invitation(1)])

        page = ListUserMemberInvitationsHandler(repo, authz()).handle(
            queries.ListUserMemberInvitationsQuery(user_id=7, actor=ACTOR)
        )

        assert [item.id for item in page.items] == [1]

    def test_get_for_recipient_only(self):
        handler = GetUserMemberInvitationHandler(
            FakeRepo(
                invitations=[_invitation(1), _invitation(2, email="other@test.de")]
            ),
            _recipient_authz(),
        )

        assert handler.handle(
            queries.GetUserMemberInvitationQuery(id=1, actor=ACTOR)
        ) == _invitation(1)
        assert (
            handler.handle(queries.GetUserMemberInvitationQuery(id=3, actor=ACTOR))
            is None
        )
        with pytest.raises(UnauthorizedError):
            handler.handle(queries.GetUserMemberInvitationQuery(id=2, actor=ACTOR))


def test_recipient_email_is_public():
    handler = GetMemberInvitationRecipientHandler(
        FakeRepo(invitations=[_invitation(1)])
    )

    assert (
        handler.handle(queries.GetMemberInvitationRecipientQuery(id=1))
        == "invited@test.de"
    )
    assert handler.handle(queries.GetMemberInvitationRecipientQuery(id=2)) is None
