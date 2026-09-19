import pytest

from project.domain.errors import ConstraintError
from project.domain.events.organization_invitation_accepted import (
    OrganizationInvitationAccepted,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.actor import Actor


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def relation(actor):
    return OrganizationRelationAggregate.create(
        actor=actor,
        source_admin_unit_id=1,
        target_admin_unit_id=2,
    )


class TestOrganizationRelationAggregateCreate:
    def test_creates_instance(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor, source_admin_unit_id=1, target_admin_unit_id=2
        )
        assert relation.id == -1
        assert relation.source_admin_unit_id == 1
        assert relation.target_admin_unit_id == 2
        assert relation.auto_verify_event_reference_requests is False
        assert relation.verify is False
        assert relation.invited is False

    def test_create_with_flags(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
            verify=True,
            invited=True,
        )
        assert relation.auto_verify_event_reference_requests is True
        assert relation.verify is True
        assert relation.invited is True

    def test_self_reference_raises_constraint_error(self, actor):
        with pytest.raises(ConstraintError):
            OrganizationRelationAggregate.create(
                actor=actor, source_admin_unit_id=1, target_admin_unit_id=1
            )

    def test_no_event_without_invitation_acceptance_info(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor, source_admin_unit_id=1, target_admin_unit_id=2
        )
        assert relation.domain_events == []

    def test_no_event_with_only_email(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            accepted_invitation_email="invited@test.de",
        )
        assert relation.domain_events == []

    def test_no_event_with_only_name(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            target_admin_unit_name="New Org",
        )
        assert relation.domain_events == []

    def test_appends_invitation_accepted_event_when_both_given(self, actor):
        relation = OrganizationRelationAggregate.create(
            actor=actor,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            accepted_invitation_email="invited@test.de",
            target_admin_unit_name="New Org",
        )
        event = relation.get_first_domain_event_by_type(OrganizationInvitationAccepted)
        assert event is not None
        assert event.inviting_admin_unit_id == 1
        assert event.new_admin_unit_id == 2
        assert event.new_admin_unit_name == "New Org"
        assert event.accepting_user_email == "invited@test.de"


class TestOrganizationRelationAggregateUpdate:
    def test_update_with_no_changes_leaves_fields_untouched(self, relation, actor):
        relation.update(actor=actor)
        assert relation.auto_verify_event_reference_requests is False
        assert relation.verify is False

    def test_update_verify(self, relation, actor):
        relation.update(actor=actor, verify=True)
        assert relation.verify is True
        assert relation.auto_verify_event_reference_requests is False

    def test_update_auto_verify_event_reference_requests(self, relation, actor):
        relation.update(actor=actor, auto_verify_event_reference_requests=True)
        assert relation.auto_verify_event_reference_requests is True
        assert relation.verify is False

    def test_update_both_flags(self, relation, actor):
        relation.update(
            actor=actor, auto_verify_event_reference_requests=True, verify=True
        )
        assert relation.auto_verify_event_reference_requests is True
        assert relation.verify is True


class TestOrganizationRelationAggregateDelete:
    def test_delete_does_not_raise(self, relation, actor):
        relation.delete(actor=actor)
