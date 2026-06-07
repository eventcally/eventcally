"""Unit tests for event organizer command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_event_organizer_handler import (
    CreateEventOrganizerHandler,
)
from project.application.command_handlers.delete_event_organizer_handler import (
    DeleteEventOrganizerHandler,
)
from project.application.command_handlers.update_event_organizer_handler import (
    UpdateEventOrganizerHandler,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# CreateEventOrganizerHandler
# ---------------------------------------------------------------------------


class TestCreateEventOrganizerHandler:
    def test_creates_organizer_and_returns_result(self, uow):
        cmd = commands.CreateEventOrganizerCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="Test Organizer",
            url=None,
            email=None,
            phone=None,
            fax=None,
            location=None,
            logo=None,
        )

        result = CreateEventOrganizerHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.event_organizers.get(result.id)
        assert created is not None
        assert created.name == "Test Organizer"

    def test_commits(self, uow):
        cmd = commands.CreateEventOrganizerCommand.model_construct(
            actor=Actor(),
            admin_unit_id=1,
            name="Organizer",
            url=None,
            email=None,
            phone=None,
            fax=None,
            location=None,
            logo=None,
        )

        CreateEventOrganizerHandler().handle(cmd, uow)

        assert uow.committed


# ---------------------------------------------------------------------------
# UpdateEventOrganizerHandler
# ---------------------------------------------------------------------------


class TestUpdateEventOrganizerHandler:
    def _seed(self, uow):
        org = EventOrganizerAggregate.create(
            actor=Actor(), admin_unit_id=1, name="Old Name"
        )
        uow.event_organizers.add(org)
        return org

    def test_updates_organizer_and_commits(self, uow):
        org = self._seed(uow)
        cmd = commands.UpdateEventOrganizerCommand.model_construct(
            actor=Actor(), id=org.id
        )

        UpdateEventOrganizerHandler().handle(cmd, uow)

        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateEventOrganizerCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateEventOrganizerHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteEventOrganizerHandler
# ---------------------------------------------------------------------------


class TestDeleteEventOrganizerHandler:
    def test_removes_organizer_and_commits(self, uow):
        org = EventOrganizerAggregate.create(
            actor=Actor(), admin_unit_id=1, name="To Delete"
        )
        uow.event_organizers.add(org)
        org_id = org.id

        cmd = commands.DeleteEventOrganizerCommand.model_construct(
            actor=Actor(), id=org_id
        )
        DeleteEventOrganizerHandler().handle(cmd, uow)

        assert uow.event_organizers.get(org_id) is None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteEventOrganizerCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            DeleteEventOrganizerHandler().handle(cmd, uow)
