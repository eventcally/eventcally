import datetime

import pytest

from project.domain.events.app_created import AppCreated
from project.domain.events.app_deleted import AppDeleted
from project.domain.events.app_installation_created import AppInstallationCreated
from project.domain.events.app_installation_deleted import AppInstallationDeleted
from project.domain.events.app_installation_permissions_updated import (
    AppInstallationPermissionsUpdated,
)
from project.domain.events.app_updated import AppUpdated
from project.domain.events.base import Event
from project.domain.events.event_created import EventCreated
from project.domain.events.event_deleted import EventDeleted
from project.domain.events.event_organizer_created import EventOrganizerCreated
from project.domain.events.event_organizer_deleted import EventOrganizerDeleted
from project.domain.events.event_organizer_updated import EventOrganizerUpdated
from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_deleted import EventPlaceDeleted
from project.domain.events.event_place_updated import EventPlaceUpdated
from project.domain.events.event_updated import EventUpdated
from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.events.webhook_delivery_created import WebhookDeliveryCreated
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types.changed_value import ChangedValue
from project.domain.types.unset_field_factory import UnsetField


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def now():
    return datetime.datetime(2024, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture
def date_def(now):
    return EventDateDefinitionValueObject(start=now)


@pytest.fixture
def event_date(now):
    return EventDateEntity(id=1, start=now)


class TestBaseEvent:
    def test_event_requires_actor(self, actor):
        event = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        assert event.actor == actor

    def test_event_has_auto_timestamp(self, actor):
        event = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime.datetime)

    def test_event_accepts_explicit_timestamp(self, actor, now):
        event = AppDeleted(actor=actor, id=1, admin_unit_id=2, timestamp=now)
        assert event.timestamp == now

    def test_has_changed_values_false_when_no_changed_fields(self, actor):
        event = AppUpdated(actor=actor, id=1, admin_unit_id=2)
        assert event.has_changed_values() is False

    def test_has_changed_values_true_when_changed_value_set(self, actor):
        cv = ChangedValue(old="old_name", new="new_name")
        event = AppUpdated(actor=actor, id=1, admin_unit_id=2, name=cv)
        assert event.has_changed_values() is True


class TestHasChangedValueMixin:
    """Tests for _has_set_changed_values branches."""

    def test_returns_true_for_changed_value_field(self, actor):
        cv = ChangedValue(old="a", new="b")
        event = AppUpdated(actor=actor, id=1, admin_unit_id=2, name=cv)
        assert event._has_set_changed_values() is True

    def test_returns_true_for_unset_default_field_set_to_value(self, actor):
        # Create an event class with a UnsetField to test the second branch
        class _EventWithUnsetField(Event):
            custom_value: str = UnsetField()

        event = _EventWithUnsetField(actor=actor, custom_value="hello")
        assert event._has_set_changed_values() is True


class TestSimpleEvents:
    def test_app_deleted(self, actor):
        event = AppDeleted(actor=actor, id=10, admin_unit_id=20)
        assert event.id == 10
        assert event.admin_unit_id == 20

    def test_app_installation_deleted(self, actor):
        event = AppInstallationDeleted(actor=actor, id=1, admin_unit_id=2, app_id=3)
        assert event.app_id == 3

    def test_event_deleted(self, actor):
        event = EventDeleted(actor=actor, id=5, admin_unit_id=6)
        assert event.id == 5

    def test_event_organizer_deleted(self, actor):
        event = EventOrganizerDeleted(actor=actor, id=7, admin_unit_id=8)
        assert event.id == 7

    def test_event_place_deleted(self, actor):
        event = EventPlaceDeleted(actor=actor, id=9, admin_unit_id=10)
        assert event.id == 9

    def test_organization_deletion_requested(self, actor):
        event = OrganizationDeletionRequested(actor=actor, id=11)
        assert event.id == 11

    def test_organization_deletion_cancelled(self, actor):
        event = OrganizationDeletionCancelled(actor=actor, id=12)
        assert event.id == 12

    def test_webhook_delivery_created(self, actor):
        event = WebhookDeliveryCreated(actor=actor, id=13)
        assert event.id == 13


class TestAppCreated:
    def test_required_fields(self, actor):
        event = AppCreated(
            actor=actor,
            id=1,
            admin_unit_id=2,
            name="My App",
            app_permissions=["read"],
        )
        assert event.name == "My App"
        assert event.app_permissions == ["read"]

    def test_optional_fields_default_to_none(self, actor):
        event = AppCreated(
            actor=actor,
            id=1,
            admin_unit_id=2,
            name="App",
            app_permissions=[],
        )
        assert event.redirect_uris is None
        assert event.scope is None
        assert event.description is None
        assert event.homepage_url is None
        assert event.setup_url is None
        assert event.webhook is None


class TestAppUpdated:
    def test_optional_fields_default_to_none(self, actor):
        event = AppUpdated(actor=actor, id=1, admin_unit_id=2)
        assert event.name is None
        assert event.app_permissions is None
        assert event.description is None

    def test_changed_value_fields_set(self, actor):
        cv = ChangedValue(old=["read"], new=["read", "write"])
        event = AppUpdated(actor=actor, id=1, admin_unit_id=2, app_permissions=cv)
        assert event.app_permissions.old == ["read"]
        assert event.app_permissions.new == ["read", "write"]


class TestAppInstallationCreated:
    def test_fields(self, actor):
        event = AppInstallationCreated(
            actor=actor, id=1, admin_unit_id=2, app_id=3, permissions=["admin"]
        )
        assert event.permissions == ["admin"]


class TestAppInstallationPermissionsUpdated:
    def test_optional_permissions_default_to_none(self, actor):
        event = AppInstallationPermissionsUpdated(
            actor=actor, id=1, admin_unit_id=2, app_id=3
        )
        assert event.permissions is None

    def test_permissions_changed_value(self, actor):
        cv = ChangedValue(old=["read"], new=["write"])
        event = AppInstallationPermissionsUpdated(
            actor=actor, id=1, admin_unit_id=2, app_id=3, permissions=cv
        )
        assert isinstance(event.permissions, ChangedValue)


class TestEventOrganizerCreated:
    def test_required_fields(self, actor):
        event = EventOrganizerCreated(
            actor=actor, id=1, admin_unit_id=2, name="Organizer"
        )
        assert event.name == "Organizer"

    def test_optional_fields_default_to_none(self, actor):
        event = EventOrganizerCreated(
            actor=actor, id=1, admin_unit_id=2, name="Organizer"
        )
        assert event.url is None
        assert event.email is None
        assert event.location is None
        assert event.logo is None


class TestEventOrganizerUpdated:
    def test_defaults_all_none(self, actor):
        event = EventOrganizerUpdated(actor=actor, id=1, admin_unit_id=2)
        assert event.name is None
        assert event.url is None
        assert event.logo is None


class TestEventPlaceCreated:
    def test_required_fields(self, actor):
        event = EventPlaceCreated(actor=actor, id=1, admin_unit_id=2, name="Venue")
        assert event.name == "Venue"

    def test_optional_fields_default_to_none(self, actor):
        event = EventPlaceCreated(actor=actor, id=1, admin_unit_id=2, name="Venue")
        assert event.description is None
        assert event.location is None
        assert event.photo is None


class TestEventPlaceUpdated:
    def test_defaults_all_none(self, actor):
        event = EventPlaceUpdated(actor=actor, id=1, admin_unit_id=2)
        assert event.name is None
        assert event.photo is None


class TestEventCreated:
    def test_required_fields(self, actor, date_def, event_date, now):
        event = EventCreated(
            actor=actor,
            id=1,
            admin_unit_id=2,
            name="My Event",
            organizer_id=3,
            event_place_id=4,
            date_definitions=[date_def],
            dates=[event_date],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        assert event.name == "My Event"
        assert event.organizer_id == 3
        assert len(event.date_definitions) == 1
        assert event.status == EventStatus.scheduled

    def test_optional_fields_default_to_none(self, actor, date_def, event_date):
        event = EventCreated(
            actor=actor,
            id=1,
            admin_unit_id=2,
            name="Event",
            organizer_id=1,
            event_place_id=1,
            date_definitions=[date_def],
            dates=[event_date],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        assert event.description is None
        assert event.tags is None
        assert event.photo is None


class TestEventUpdated:
    def test_defaults_all_none(self, actor):
        event = EventUpdated(actor=actor, id=1, admin_unit_id=2)
        assert event.name is None
        assert event.organizer_id is None
        assert event.photo is None
        assert event.status is None
