"""Unit tests for application read models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from project.application.read_models.event_read_model import (
    AdminUnitReadModel,
    EventDateDefinitionReadModel,
    EventReadModel,
    OrganizerReadModel,
)


class TestEventReadModel:
    def _build(self, name="Fest"):
        date_def = EventDateDefinitionReadModel(
            start=datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
        )
        admin_unit = AdminUnitReadModel(id=1, name="City")
        organizer = OrganizerReadModel(id=2, name="Club")
        return EventReadModel(
            id=10,
            name=name,
            min_start_definition=date_def,
            is_recurring=False,
            admin_unit=admin_unit,
            organizer=organizer,
        )

    def test_construction(self):
        model = self._build()
        assert model.id == 10
        assert model.name == "Fest"
        assert model.is_recurring is False

    def test_frozen_raises_on_mutation(self):
        model = self._build()
        with pytest.raises((ValidationError, TypeError)):
            model.name = "New Name"

    def test_admin_unit_fields(self):
        model = self._build()
        assert model.admin_unit.id == 1
        assert model.admin_unit.name == "City"

    def test_organizer_fields(self):
        model = self._build()
        assert model.organizer.id == 2
        assert model.organizer.name == "Club"

    def test_min_start_definition_fields(self):
        model = self._build()
        assert model.min_start_definition.start.year == 2024


class TestEventDateDefinitionReadModel:
    def test_defaults(self):
        dd = EventDateDefinitionReadModel(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        assert dd.end is None
        assert dd.allday is False
        assert dd.recurrence_rule is None

    def test_frozen_on_allday(self):
        dd = EventDateDefinitionReadModel(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc), allday=True
        )
        with pytest.raises((ValidationError, TypeError)):
            dd.allday = False


class TestAdminUnitReadModel:
    def test_construction(self):
        m = AdminUnitReadModel(id=5, name="Org")
        assert m.id == 5
        assert m.name == "Org"

    def test_frozen(self):
        m = AdminUnitReadModel(id=5, name="Org")
        with pytest.raises((ValidationError, TypeError)):
            m.name = "New"


class TestOrganizerReadModel:
    def test_construction(self):
        m = OrganizerReadModel(id=3, name="Club")
        assert m.id == 3

    def test_frozen(self):
        m = OrganizerReadModel(id=3, name="Club")
        with pytest.raises((ValidationError, TypeError)):
            m.id = 99
