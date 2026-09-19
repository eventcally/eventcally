"""Unit tests for CreateOrganizationHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.create_organization_handler import (
    CreateOrganizationHandler,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId
from tests.application.conftest import ACTOR, grant_permission


def _make_organization(
    uow, can_verify_other=False, incoming_reference_requests_allowed=False
):
    org = OrganizationAggregate.create(
        actor=Actor(), name="Existing Org", short_name="existing_org"
    )
    org.can_verify_other = can_verify_other
    org.incoming_reference_requests_allowed = incoming_reference_requests_allowed
    uow.organizations.add(org)
    return org


def _add_actor_user(uow, email="actor@test.de"):
    from project.domain.models.aggregates.user_aggregate import UserAggregate

    user = UserAggregate(id=ACTOR.user_id, email=email, locale=None)
    uow.users.add(user)
    return user


class TestCreateOrganizationHandlerPlain:
    def test_creates_organization_member_and_organizer(self, uow):
        _add_actor_user(uow)
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR, name="My Crew", short_name="my_crew"
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.id > 0
        assert result.verified is False

        organization = uow.organizations.get(result.id)
        assert organization.name == "My Crew"
        assert organization.short_name == "my_crew"

        members = list(uow.organization_members._store.values())
        assert len(members) == 1
        assert members[0].admin_unit_id == result.id
        assert members[0].user_id == ACTOR.user_id
        assert set(members[0].roles) == {"admin", "event_verifier"}

        organizers = list(uow.event_organizers._store.values())
        assert len(organizers) == 1
        assert organizers[0].admin_unit_id == result.id
        assert organizers[0].name == "My Crew"

    def test_no_location_no_place_created(self, uow):
        _add_actor_user(uow)
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR, name="My Crew", short_name="my_crew"
        )

        CreateOrganizationHandler().handle(cmd, uow)

        assert list(uow.event_places._store.values()) == []

    def test_location_creates_place(self, uow):
        _add_actor_user(uow)
        location = LocationValueObject(city="Goslar")
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR, name="My Crew", short_name="my_crew", location=location
        )

        CreateOrganizationHandler().handle(cmd, uow)

        places = list(uow.event_places._store.values())
        assert len(places) == 1
        assert places[0].name == "Goslar"
        assert places[0].location == location

    def test_no_relation_without_invitation_or_current_admin_unit(self, uow):
        _add_actor_user(uow)
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR, name="My Crew", short_name="my_crew"
        )

        CreateOrganizationHandler().handle(cmd, uow)

        assert list(uow.organization_relations._store.values()) == []

    def test_app_installation_actor_raises_unauthorized_error(self, uow):
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=Actor(app_installation_id=1), name="My Crew", short_name="my_crew"
        )

        with pytest.raises(UnauthorizedError):
            CreateOrganizationHandler().handle(cmd, uow)

        assert list(uow.organizations._store.values()) == []

    def test_unknown_actor_user_raises_unauthorized_error(self, uow):
        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR, name="My Crew", short_name="my_crew"
        )

        with pytest.raises(UnauthorizedError):
            CreateOrganizationHandler().handle(cmd, uow)

        assert list(uow.organizations._store.values()) == []


class TestCreateOrganizationHandlerInvitation:
    def _make_invitation(
        self,
        uow,
        inviting_admin_unit_id: ObjectId,
        email="invited@test.de",
        relation_verify=True,
        relation_auto_verify_event_reference_requests=True,
    ):
        invitation = AdminUnitInvitationAggregate.create(
            actor=Actor(),
            admin_unit_id=inviting_admin_unit_id,
            email=email,
            relation_verify=relation_verify,
            relation_auto_verify_event_reference_requests=(
                relation_auto_verify_event_reference_requests
            ),
        )
        uow.organization_invitations.add(invitation)
        return invitation

    def test_creates_relation_and_removes_invitation(self, uow):
        _add_actor_user(uow, email="invited@test.de")
        inviting_org = _make_organization(
            uow, can_verify_other=True, incoming_reference_requests_allowed=True
        )
        invitation = self._make_invitation(uow, inviting_org.id)
        invitation_id = invitation.id

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            invitation_id=invitation_id,
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.verified is True
        relations = list(uow.organization_relations._store.values())
        assert len(relations) == 1
        relation = relations[0]
        assert relation.source_admin_unit_id == inviting_org.id
        assert relation.target_admin_unit_id == result.id
        assert relation.invited is True
        assert relation.verify is True
        assert relation.auto_verify_event_reference_requests is True

        assert uow.organization_invitations.get(invitation_id) is None

    def test_masks_flags_against_inviting_org(self, uow):
        _add_actor_user(uow, email="invited@test.de")
        inviting_org = _make_organization(
            uow, can_verify_other=False, incoming_reference_requests_allowed=False
        )
        invitation = self._make_invitation(uow, inviting_org.id)

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            invitation_id=invitation.id,
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.verified is False
        relation = list(uow.organization_relations._store.values())[0]
        assert relation.verify is False
        assert relation.auto_verify_event_reference_requests is False

    def test_wrong_actor_raises_unauthorized_error(self, uow):
        _add_actor_user(uow, email="someone-else@test.de")
        inviting_org = _make_organization(uow, can_verify_other=True)
        invitation = self._make_invitation(
            uow, inviting_org.id, email="invited@test.de"
        )

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            invitation_id=invitation.id,
        )

        with pytest.raises(UnauthorizedError):
            CreateOrganizationHandler().handle(cmd, uow)


class TestCreateOrganizationHandlerEmbeddedRelation:
    def test_verify_flag_creates_relation(self, uow):
        _add_actor_user(uow)
        current_org = _make_organization(uow, can_verify_other=True)
        grant_permission(uow, current_org.id, "outgoing_organization_relations:write")

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            current_admin_unit_id=current_org.id,
            embedded_relation_verify=True,
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.verified is True
        relation = list(uow.organization_relations._store.values())[0]
        assert relation.source_admin_unit_id == current_org.id
        assert relation.target_admin_unit_id == result.id
        assert relation.verify is True
        assert relation.invited is False

    def test_auto_verify_flag_creates_relation(self, uow):
        _add_actor_user(uow)
        current_org = _make_organization(uow, incoming_reference_requests_allowed=True)
        grant_permission(uow, current_org.id, "outgoing_organization_relations:write")

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            current_admin_unit_id=current_org.id,
            embedded_relation_auto_verify_event_reference_requests=True,
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.verified is False
        relation = list(uow.organization_relations._store.values())[0]
        assert relation.auto_verify_event_reference_requests is True

    def test_flags_masked_to_false_creates_no_relation(self, uow):
        _add_actor_user(uow)
        current_org = _make_organization(
            uow, can_verify_other=False, incoming_reference_requests_allowed=False
        )
        grant_permission(uow, current_org.id, "outgoing_organization_relations:write")

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            current_admin_unit_id=current_org.id,
            embedded_relation_verify=True,
            embedded_relation_auto_verify_event_reference_requests=True,
        )

        result = CreateOrganizationHandler().handle(cmd, uow)

        assert result.verified is False
        assert list(uow.organization_relations._store.values()) == []

    def test_actor_without_relation_permission_raises(self, uow):
        _add_actor_user(uow)
        current_org = _make_organization(uow, can_verify_other=True)

        cmd = commands.CreateOrganizationCommand.model_construct(
            actor=ACTOR,
            name="New Org",
            short_name="new_org",
            current_admin_unit_id=current_org.id,
            embedded_relation_verify=True,
        )

        with pytest.raises(UnauthorizedError):
            CreateOrganizationHandler().handle(cmd, uow)

        assert list(uow.organization_relations._store.values()) == []
