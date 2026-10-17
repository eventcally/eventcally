"""Access query handlers — fake repository and permission reader, no database."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    AnyOrganizationAcceptsReferenceRequestsHandler,
    CanRequestVerificationHandler,
    GetApiKeyByHashHandler,
    GetCurrentOrganizationHandler,
    GetManageableOrganizationHandler,
    GetOrganizationSettingsHandler,
    GetResourceOwnerHandler,
    HasOtherAdminHandler,
    IsOrganizationNameTakenHandler,
    IsOrganizationShortNameTakenHandler,
    ListManageableOrganizationsHandler,
)
from project.application.read_models.access_helper_read_models import (
    MailRecipientReadModel,
    ManageMenuOptionsReadModel,
    MemberGrantsReadModel,
)
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
    OrganizationSettingsReadModel,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader

ORGANIZATIONS = {
    i: CurrentOrganizationReadModel(id=i, name=f"Org {i}") for i in (1, 2, 3)
}


class FakeAccessRepo(AbstractAccessReadRepository):
    def get_organization(self, admin_unit_id):
        return ORGANIZATIONS.get(admin_unit_id)

    def list_organizations(self, admin_unit_ids):
        ids = list(ORGANIZATIONS) if admin_unit_ids is None else admin_unit_ids
        return [ORGANIZATIONS[i] for i in ids]

    def member_organization_ids(self, user_id):
        return [3, 1] if user_id == 7 else []

    def get_resource_owner(self, kind, resource_id):
        return (kind.value, resource_id)

    def has_other_admin(self, admin_unit_id, user_id):
        return (admin_unit_id, user_id) == (1, 2)

    def get_api_key_by_hash(self, key_hash):
        return key_hash

    def is_name_taken(self, name, exclude_id):
        return (name, exclude_id) == ("taken", None)

    def is_short_name_taken(self, short_name, exclude_id):
        return (short_name, exclude_id) == ("short", 4)

    def can_request_verification(self, source, target):
        return (source, target) == (1, 2)

    def any_accepts_reference_requests(self, exclude_admin_unit_id):
        return exclude_admin_unit_id == 1

    def get_settings(self, admin_unit_id):
        return OrganizationSettingsReadModel(id=admin_unit_id, name="Settings")

    def count_incoming_badges(self, admin_unit_id):
        return ManageMenuOptionsReadModel(
            reference_requests_incoming_badge=admin_unit_id,
            verification_requests_incoming_badge=1,
        )

    def member_grants(self, admin_unit_id, user_id):
        return MemberGrantsReadModel(roles=["admin"], permissions=[f"{user_id}:read"])

    def event_report_recipients(self, admin_unit_id, permission):
        return [MailRecipientReadModel(id=admin_unit_id, email=permission)]


def _authz(**reader):
    return ActorAuthorizationService(FakeReader(**reader))


def test_pass_through_handlers():
    repo = FakeAccessRepo()

    assert (
        GetCurrentOrganizationHandler(repo)
        .handle(queries.GetCurrentOrganizationQuery(id=2))
        .name
        == "Org 2"
    )
    assert GetResourceOwnerHandler(repo).handle(
        queries.GetResourceOwnerQuery(kind=queries.ResourceKind.event, id=5)
    ) == ("event", 5)
    assert HasOtherAdminHandler(repo).handle(
        queries.HasOtherAdminQuery(admin_unit_id=1, user_id=2)
    )
    assert (
        GetApiKeyByHashHandler(repo).handle(
            queries.GetApiKeyByHashQuery(key_hash="abc")
        )
        == "abc"
    )
    assert IsOrganizationNameTakenHandler(repo).handle(
        queries.IsOrganizationNameTakenQuery(name="taken")
    )
    assert IsOrganizationShortNameTakenHandler(repo).handle(
        queries.IsOrganizationShortNameTakenQuery(short_name="short", exclude_id=4)
    )
    assert CanRequestVerificationHandler(repo).handle(
        queries.CanRequestVerificationQuery(
            source_admin_unit_id=1, target_admin_unit_id=2
        )
    )
    assert AnyOrganizationAcceptsReferenceRequestsHandler(repo).handle(
        queries.AnyOrganizationAcceptsReferenceRequestsQuery(exclude_admin_unit_id=1)
    )


class TestManageableOrganizations:
    def _list(self, actor, member_only=False, **reader):
        handler = ListManageableOrganizationsHandler(FakeAccessRepo(), _authz(**reader))
        query = queries.ListManageableOrganizationsQuery(
            actor=actor, member_only=member_only
        )
        return [o.id for o in handler.handle(query)]

    def test_members_get_their_organizations_in_membership_order(self):
        assert self._list(Actor(user_id=7)) == [3, 1]

    def test_platform_admins_get_everything_unless_members_only(self):
        assert self._list(Actor(user_id=7), admins=[7]) == [1, 2, 3]
        assert self._list(Actor(user_id=7), member_only=True, admins=[7]) == [3, 1]

    @pytest.mark.parametrize("actor", [None, Actor(), Actor(app_installation_id=5)])
    def test_anonymous_actors_and_installations_manage_nothing(self, actor):
        assert self._list(actor) == []

    def test_a_single_organization_follows_the_same_rule(self):
        handler = GetManageableOrganizationHandler(FakeAccessRepo(), _authz())
        member_handler = GetManageableOrganizationHandler(
            FakeAccessRepo(), _authz(admins=[8])
        )

        def get(h, organization_id, user_id):
            return h.handle(
                queries.GetManageableOrganizationQuery(
                    id=organization_id, actor=Actor(user_id=user_id)
                )
            )

        assert get(handler, 1, 7).id == 1
        assert get(handler, 2, 7) is None
        assert get(member_handler, 2, 8).id == 2
        assert get(member_handler, 4711, 8) is None
        assert (
            handler.handle(queries.GetManageableOrganizationQuery(id=1, actor=None))
            is None
        )


class TestOrganizationSettings:
    def _handle(self, actor, organization_id=1, **reader):
        handler = GetOrganizationSettingsHandler(FakeAccessRepo(), _authz(**reader))
        return handler.handle(
            queries.GetOrganizationSettingsQuery(id=organization_id, actor=actor)
        )

    def test_members_and_platform_admins_may_read(self):
        assert self._handle(Actor(user_id=7)).id == 1
        assert self._handle(Actor(user_id=9), organization_id=2, admins=[9]).id == 2

    @pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
    def test_everyone_else_is_refused(self, actor):
        with pytest.raises(UnauthorizedError):
            self._handle(actor)
