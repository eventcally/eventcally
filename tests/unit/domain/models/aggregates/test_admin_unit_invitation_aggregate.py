import pytest

from project.domain.events import OrganizationInvitationCreated
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestAdminUnitInvitationAggregateCreate:
    def test_creates_instance(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor,
            admin_unit_id=2,
            email="invitee@test.de",
            admin_unit_name="Future Org",
            relation_auto_verify_event_reference_requests=True,
            relation_verify=True,
        )
        assert invitation.id == -1
        assert invitation.admin_unit_id == 2
        assert invitation.email == "invitee@test.de"
        assert invitation.admin_unit_name == "Future Org"
        assert invitation.relation_auto_verify_event_reference_requests is True
        assert invitation.relation_verify is True

    def test_optional_fields_default(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        assert invitation.admin_unit_name is None
        assert invitation.relation_auto_verify_event_reference_requests is False
        assert invitation.relation_verify is False

    def test_raises_organization_invitation_created_event(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        events = [
            e
            for e in invitation.domain_events
            if isinstance(e, OrganizationInvitationCreated)
        ]
        assert len(events) == 1
        assert events[0].admin_unit_id == 2
        assert events[0].email == "invitee@test.de"


class TestAdminUnitInvitationAggregateUpdate:
    def test_update_changes_fields(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        invitation.update(
            actor=actor,
            admin_unit_name="New Name",
            relation_auto_verify_event_reference_requests=True,
            relation_verify=True,
        )
        assert invitation.admin_unit_name == "New Name"
        assert invitation.relation_auto_verify_event_reference_requests is True
        assert invitation.relation_verify is True

    def test_update_with_no_changes_leaves_fields_untouched(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor,
            admin_unit_id=2,
            email="invitee@test.de",
            admin_unit_name="Name",
        )
        invitation.update(actor=actor)
        assert invitation.admin_unit_name == "Name"
        assert invitation.relation_auto_verify_event_reference_requests is False
        assert invitation.relation_verify is False


class TestAdminUnitInvitationAggregateDelete:
    def test_delete_does_not_raise(self, actor):
        invitation = AdminUnitInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        invitation.delete(actor=actor)
