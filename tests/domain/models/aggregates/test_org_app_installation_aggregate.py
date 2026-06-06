import pytest

from project.domain.events.app_installation_created import AppInstallationCreated
from project.domain.events.app_installation_deleted import AppInstallationDeleted
from project.domain.events.app_installation_permissions_updated import (
    AppInstallationPermissionsUpdated,
)
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.types.changed_value import ChangedValue


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def installation(actor):
    return OrganisationAppInstallationAggregate.create(
        actor=actor,
        admin_unit_id=2,
        app_id=3,
        permissions=["read"],
    )


class TestOrganisationAppInstallationAggregateCreate:
    def test_creates_instance(self, actor):
        inst = OrganisationAppInstallationAggregate.create(
            actor=actor, admin_unit_id=2, app_id=3, permissions=["admin"]
        )
        assert inst.admin_unit_id == 2
        assert inst.app_id == 3
        assert inst.permissions == ["admin"]

    def test_appends_created_event(self, actor):
        inst = OrganisationAppInstallationAggregate.create(
            actor=actor, admin_unit_id=2, app_id=3, permissions=[]
        )
        assert len(inst.domain_events) == 1
        assert isinstance(inst.domain_events[0], AppInstallationCreated)

    def test_created_event_has_correct_ids(self, actor):
        inst = OrganisationAppInstallationAggregate.create(
            actor=actor, admin_unit_id=2, app_id=3, permissions=["write"]
        )
        event = inst.domain_events[0]
        assert event.admin_unit_id == 2
        assert event.app_id == 3
        assert event.permissions == ["write"]


class TestOrganisationAppInstallationAggregateUpdatePermissions:
    def test_update_permissions_with_change_appends_event(self, installation, actor):
        initial_count = len(installation.domain_events)
        installation.update_permissions(actor=actor, permissions=["read", "write"])
        assert len(installation.domain_events) == initial_count + 1
        assert isinstance(
            installation.domain_events[-1], AppInstallationPermissionsUpdated
        )

    def test_update_permissions_sets_changed_value(self, installation, actor):
        installation.update_permissions(actor=actor, permissions=["read", "write"])
        event = installation.domain_events[-1]
        assert isinstance(event.permissions, ChangedValue)
        assert event.permissions.old == ["read"]
        assert event.permissions.new == ["read", "write"]

    def test_update_permissions_with_same_value_appends_no_event(
        self, installation, actor
    ):
        initial_count = len(installation.domain_events)
        installation.update_permissions(actor=actor, permissions=["read"])
        assert len(installation.domain_events) == initial_count

    def test_update_permissions_updates_field(self, installation, actor):
        installation.update_permissions(actor=actor, permissions=["admin"])
        assert installation.permissions == ["admin"]


class TestOrganisationAppInstallationAggregateDelete:
    def test_delete_appends_deleted_event(self, installation, actor):
        initial_count = len(installation.domain_events)
        installation.delete(actor=actor)
        assert len(installation.domain_events) == initial_count + 1
        assert isinstance(installation.domain_events[-1], AppInstallationDeleted)

    def test_deleted_event_ids(self, installation, actor):
        installation.delete(actor=actor)
        event = installation.domain_events[-1]
        assert event.id == installation.id
        assert event.admin_unit_id == installation.admin_unit_id
        assert event.app_id == installation.app_id
