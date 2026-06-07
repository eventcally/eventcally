"""Unit tests for event place command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_event_place_handler import (
    CreateEventPlaceHandler,
)
from project.application.command_handlers.delete_event_place_handler import (
    DeleteEventPlaceHandler,
)
from project.application.command_handlers.update_event_place_handler import (
    UpdateEventPlaceHandler,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# CreateEventPlaceHandler
# ---------------------------------------------------------------------------


class TestCreateEventPlaceHandler:
    def test_creates_place_and_returns_result(self, uow):
        cmd = commands.CreateEventPlaceCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="Test Place",
            url=None,
            description=None,
            location=None,
            photo=None,
        )

        result = CreateEventPlaceHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.event_places.get(result.id)
        assert created is not None
        assert created.name == "Test Place"

    def test_commits(self, uow):
        cmd = commands.CreateEventPlaceCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="Place",
            url=None,
            description=None,
            location=None,
            photo=None,
        )

        CreateEventPlaceHandler().handle(cmd, uow)

        assert uow.committed


# ---------------------------------------------------------------------------
# UpdateEventPlaceHandler
# ---------------------------------------------------------------------------


class TestUpdateEventPlaceHandler:
    def _seed(self, uow):
        place = EventPlaceAggregate.create(
            actor=Actor(), admin_unit_id=1, name="Old Place"
        )
        uow.event_places.add(place)
        return place

    def test_updates_place_and_commits(self, uow):
        place = self._seed(uow)
        cmd = commands.UpdateEventPlaceCommand.model_construct(
            actor=Actor(), id=place.id
        )

        UpdateEventPlaceHandler().handle(cmd, uow)

        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateEventPlaceCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            UpdateEventPlaceHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteEventPlaceHandler
# ---------------------------------------------------------------------------


class TestDeleteEventPlaceHandler:
    def test_removes_place_and_commits(self, uow):
        place = EventPlaceAggregate.create(
            actor=Actor(), admin_unit_id=1, name="To Delete"
        )
        uow.event_places.add(place)
        place_id = place.id

        cmd = commands.DeleteEventPlaceCommand.model_construct(
            actor=Actor(), id=place_id
        )
        DeleteEventPlaceHandler().handle(cmd, uow)

        assert uow.event_places.get(place_id) is None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteEventPlaceCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            DeleteEventPlaceHandler().handle(cmd, uow)
