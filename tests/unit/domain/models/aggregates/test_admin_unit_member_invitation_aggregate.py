import pytest

from project.domain.events import MemberInvitationCreated
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


class TestAdminUnitMemberInvitationAggregateCreate:
    def test_creates_instance(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de", roles=["admin"]
        )
        assert invitation.id == -1
        assert invitation.admin_unit_id == 2
        assert invitation.email == "invitee@test.de"
        assert invitation.roles == ["admin"]

    def test_roles_default_to_empty_list(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        assert invitation.roles == []

    def test_raises_member_invitation_created_event(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        events = [
            e
            for e in invitation.domain_events
            if isinstance(e, MemberInvitationCreated)
        ]
        assert len(events) == 1
        assert events[0].admin_unit_id == 2
        assert events[0].email == "invitee@test.de"


class TestAdminUnitMemberInvitationAggregateUpdate:
    def test_update_changes_roles(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de", roles=["admin"]
        )
        invitation.update(actor=actor, roles=["event_verifier"])
        assert invitation.roles == ["event_verifier"]

    def test_update_with_no_changes_leaves_roles_untouched(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de", roles=["admin"]
        )
        invitation.update(actor=actor)
        assert invitation.roles == ["admin"]


class TestAdminUnitMemberInvitationAggregateDelete:
    def test_delete_does_not_raise(self, actor):
        invitation = AdminUnitMemberInvitationAggregate.create(
            actor=actor, admin_unit_id=2, email="invitee@test.de"
        )
        invitation.delete(actor=actor)
