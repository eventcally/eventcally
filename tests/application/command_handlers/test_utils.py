"""Unit tests for command handler utility functions."""

from datetime import datetime, timezone

import pytest

from project.application.command_handlers.app_utils import ensure_app_exists
from project.application.command_handlers.event_organizer_utils import (
    ensure_event_organizer_exists,
)
from project.application.command_handlers.event_place_utils import (
    ensure_event_place_exists,
)
from project.application.command_handlers.event_utils import ensure_event_exists
from project.application.command_handlers.organization_app_installation_utils import (
    ensure_organization_app_installation_exists,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)

# ---------------------------------------------------------------------------
# ensure_event_exists
# ---------------------------------------------------------------------------


class TestEnsureEventExists:
    def _make_event(self, uow):
        org = EventOrganizerAggregate.create(actor=Actor(), admin_unit_id=1, name="Org")
        uow.event_organizers.add(org)
        place = EventPlaceAggregate.create(actor=Actor(), admin_unit_id=1, name="Place")
        uow.event_places.add(place)
        event = EventAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="E",
            organizer_id=org.id,
            event_place_id=place.id,
            date_definitions=[
                EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
            ],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        uow.events.add(event)
        return event

    def test_returns_event_when_found(self, uow):
        event = self._make_event(uow)
        result = ensure_event_exists(event.id, uow)
        assert result is event

    def test_raises_not_found_when_missing(self, uow):
        with pytest.raises(NotFoundError):
            ensure_event_exists(9999, uow)


# ---------------------------------------------------------------------------
# ensure_event_organizer_exists
# ---------------------------------------------------------------------------


class TestEnsureEventOrganizerExists:
    def test_returns_organizer_when_found(self, uow):
        org = EventOrganizerAggregate.create(actor=Actor(), admin_unit_id=1, name="Org")
        uow.event_organizers.add(org)

        result = ensure_event_organizer_exists(org.id, uow)
        assert result is org

    def test_raises_not_found_when_missing(self, uow):
        with pytest.raises(NotFoundError):
            ensure_event_organizer_exists(9999, uow)


# ---------------------------------------------------------------------------
# ensure_event_place_exists
# ---------------------------------------------------------------------------


class TestEnsureEventPlaceExists:
    def test_returns_place_when_found(self, uow):
        place = EventPlaceAggregate.create(actor=Actor(), admin_unit_id=1, name="P")
        uow.event_places.add(place)

        result = ensure_event_place_exists(place.id, uow)
        assert result is place

    def test_raises_not_found_when_missing(self, uow):
        with pytest.raises(NotFoundError):
            ensure_event_place_exists(9999, uow)


# ---------------------------------------------------------------------------
# ensure_app_exists
# ---------------------------------------------------------------------------


class TestEnsureAppExists:
    def test_returns_app_when_found(self, uow):
        app = AppAggregate.create(
            actor=Actor(), admin_unit_id=1, name="A", app_permissions=["x"]
        )
        uow.apps.add(app)

        result = ensure_app_exists(app.id, uow)
        assert result is app

    def test_raises_not_found_when_missing(self, uow):
        with pytest.raises(NotFoundError):
            ensure_app_exists(9999, uow)


# ---------------------------------------------------------------------------
# ensure_organization_app_installation_exists
# ---------------------------------------------------------------------------


class TestEnsureOrgAppInstallationExists:
    def test_returns_installation_when_found(self, uow):
        inst = OrganisationAppInstallationAggregate.create(
            actor=Actor(), admin_unit_id=1, app_id=1, permissions=[]
        )
        uow.organization_app_installations.add(inst)

        result = ensure_organization_app_installation_exists(inst.id, uow)
        assert result is inst

    def test_raises_not_found_when_missing(self, uow):
        with pytest.raises(NotFoundError):
            ensure_organization_app_installation_exists(9999, uow)
