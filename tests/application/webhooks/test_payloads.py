"""Unit tests for webhook payload from_event() methods."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from project.application.webhooks.payloads.app_installation_created_payload import (
    AppInstallationCreatedPayload,
)
from project.application.webhooks.payloads.app_installation_deleted_payload import (
    AppInstallationDeletedPayload,
)
from project.application.webhooks.payloads.app_installation_permissions_updated_payload import (
    AppInstallationPermissionsUpdatedPayload,
)
from project.application.webhooks.payloads.event_organizer_created_payload import (
    EventOrganizerCreatedPayload,
)
from project.application.webhooks.payloads.event_organizer_deleted_payload import (
    EventOrganizerDeletedPayload,
)
from project.application.webhooks.payloads.event_organizer_updated_payload import (
    EventOrganizerUpdatedPayload,
)
from project.application.webhooks.payloads.event_place_created_payload import (
    EventPlaceCreatedPayload,
)
from project.application.webhooks.payloads.event_place_deleted_payload import (
    EventPlaceDeletedPayload,
)
from project.application.webhooks.payloads.event_place_updated_payload import (
    EventPlaceUpdatedPayload,
)
from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.application.webhooks.payloads.nested.payload_image import PayloadImage
from project.application.webhooks.payloads.nested.payload_location import (
    PayloadLocation,
)
from project.application.webhooks.webhook_mapper_context import WebhookMapperContext
from project.domain import events
from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types.changed_value import ChangedValue

# ---------------------------------------------------------------------------
# Context fixture — mock url_for to avoid Flask app context requirement
# ---------------------------------------------------------------------------


@pytest.fixture()
def ctx():
    url_provider = MagicMock()
    url_provider.get_image_url.return_value = "http://img.example.com/1"
    yield WebhookMapperContext(url_provider=url_provider)


# ---------------------------------------------------------------------------
# PayloadImage / PayloadLocation null guards
# ---------------------------------------------------------------------------


class TestNestedPayloadNullGuards:
    def test_payload_actor_from_none_returns_none(self, ctx):
        assert PayloadActor.from_event(None, ctx) is None

    def test_payload_actor_from_event_maps_fields(self, ctx):
        actor = Actor(user_id=5, app_installation_id=7)
        payload = PayloadActor.from_event(actor, ctx)
        assert payload.user_id == 5
        assert payload.app_installation_id == 7

    def test_payload_image_from_none_returns_none(self, ctx):
        assert PayloadImage.from_event(None, ctx) is None

    def test_payload_image_from_event_maps_fields(self, ctx):
        img = ImageForEvent(
            id=1,
            hash=123,
            encoding_format="image/png",
            copyright_text="(c)",
            license_id=9,
        )
        payload = PayloadImage.from_event(img, ctx)
        assert payload.url == "http://img.example.com/1"
        assert payload.encoding_format == "image/png"
        assert payload.copyright_text == "(c)"
        assert payload.license_id == 9

    def test_payload_location_from_none_returns_none(self, ctx):
        assert PayloadLocation.from_event(None, ctx) is None

    def test_payload_location_from_event_maps_fields(self, ctx):
        location = LocationValueObject(
            street="Main",
            postalCode="12345",
            city="Berlin",
            state="BE",
            country="DE",
            latitude=52.5,
            longitude=13.4,
        )
        payload = PayloadLocation.from_event(location, ctx)
        assert payload.street == "Main"
        assert payload.postal_code == "12345"
        assert payload.city == "Berlin"
        assert payload.state == "BE"
        assert payload.country == "DE"
        assert payload.latitude == 52.5
        assert payload.longitude == 13.4


# ---------------------------------------------------------------------------
# EventOrganizer payloads
# ---------------------------------------------------------------------------


class TestEventOrganizerPayloads:
    def _make_created_event(self):
        return events.EventOrganizerCreated(
            actor=Actor(),
            id=1,
            admin_unit_id=2,
            name="Org",
            url="http://org.com",
            email="a@b.com",
            phone="123",
            fax=None,
            location=None,
            logo=None,
        )

    def test_event_organizer_created_payload(self, ctx):
        ev = self._make_created_event()
        payload = EventOrganizerCreatedPayload.from_event(ev, ctx)
        assert payload.id == 1
        assert payload.organization_id == 2
        assert payload.name == "Org"
        assert payload.url == "http://org.com"

    def test_event_organizer_updated_payload(self, ctx):
        ev = events.EventOrganizerUpdated(
            actor=Actor(),
            id=3,
            admin_unit_id=2,
            name=ChangedValue(old="Org", new="Updated"),
        )
        payload = EventOrganizerUpdatedPayload.from_event(ev, ctx)
        assert payload.id == 3
        assert payload.organization_id == 2

    def test_event_organizer_deleted_payload(self, ctx):
        ev = events.EventOrganizerDeleted(actor=Actor(), id=5, admin_unit_id=2)
        payload = EventOrganizerDeletedPayload.from_event(ev, ctx)
        assert payload.id == 5
        assert payload.organization_id == 2


# ---------------------------------------------------------------------------
# EventPlace payloads
# ---------------------------------------------------------------------------


class TestEventPlacePayloads:
    def test_event_place_created_payload(self, ctx):
        ev = events.EventPlaceCreated(
            actor=Actor(),
            id=10,
            admin_unit_id=3,
            name="Place",
            url=None,
            description=None,
            location=None,
            photo=None,
        )
        payload = EventPlaceCreatedPayload.from_event(ev, ctx)
        assert payload.id == 10
        assert payload.organization_id == 3
        assert payload.name == "Place"

    def test_event_place_updated_payload(self, ctx):
        ev = events.EventPlaceUpdated(
            actor=Actor(),
            id=11,
            admin_unit_id=3,
            name=ChangedValue(old="Place", new="P2"),
        )
        payload = EventPlaceUpdatedPayload.from_event(ev, ctx)
        assert payload.id == 11

    def test_event_place_deleted_payload(self, ctx):
        ev = events.EventPlaceDeleted(actor=Actor(), id=12, admin_unit_id=3)
        payload = EventPlaceDeletedPayload.from_event(ev, ctx)
        assert payload.id == 12


# ---------------------------------------------------------------------------
# AppInstallation payloads
# ---------------------------------------------------------------------------


class TestAppInstallationPayloads:
    def test_app_installation_created_payload(self, ctx):
        ev = events.AppInstallationCreated(
            actor=Actor(),
            id=20,
            admin_unit_id=4,
            app_id=100,
            permissions=["events:read"],
        )
        payload = AppInstallationCreatedPayload.from_event(ev, ctx)
        assert payload.id == 20
        assert payload.app_id == 100
        assert payload.organization_id == 4
        assert payload.permissions == ["events:read"]

    def test_app_installation_deleted_payload(self, ctx):
        ev = events.AppInstallationDeleted(
            actor=Actor(), id=21, admin_unit_id=4, app_id=100
        )
        payload = AppInstallationDeletedPayload.from_event(ev, ctx)
        assert payload.id == 21
        assert payload.app_id == 100

    def test_app_installation_permissions_updated_payload(self, ctx):
        ev = events.AppInstallationPermissionsUpdated(
            actor=Actor(),
            id=22,
            admin_unit_id=4,
            app_id=100,
            permissions=ChangedValue(old=[], new=["events:read"]),
        )
        # Known production behavior: from_event passes ChangedValue directly into
        # a list[str] payload field and triggers validation.
        with pytest.raises(ValidationError):
            AppInstallationPermissionsUpdatedPayload.from_event(ev, ctx)
