from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.entities.actor import Actor


class TestOrganisationMemberAggregateCreate:
    def test_creates_instance(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        assert member.id == -1
        assert member.admin_unit_id == 1
        assert member.user_id == 2
        assert member.roles == ["admin"]

    def test_roles_default_to_empty_list(self):
        member = OrganisationMemberAggregate.create(admin_unit_id=1, user_id=2)
        assert member.roles == []


class TestOrganisationMemberAggregateAddRoles:
    def test_adds_new_roles(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        member.add_roles(["event_verifier"])
        assert member.roles == ["admin", "event_verifier"]

    def test_does_not_duplicate_existing_roles(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        member.add_roles(["admin"])
        assert member.roles == ["admin"]

    def test_add_roles_with_empty_list_is_noop(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        member.add_roles([])
        assert member.roles == ["admin"]


class TestOrganisationMemberAggregateUpdate:
    def test_update_changes_roles(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        member.update(actor=Actor(user_id=2), roles=["event_verifier"])
        assert member.roles == ["event_verifier"]

    def test_update_with_no_changes_leaves_roles_untouched(self):
        member = OrganisationMemberAggregate.create(
            admin_unit_id=1, user_id=2, roles=["admin"]
        )
        member.update(actor=Actor(user_id=2))
        assert member.roles == ["admin"]
