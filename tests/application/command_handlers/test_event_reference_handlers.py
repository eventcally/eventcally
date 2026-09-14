"""Unit tests for event reference command handlers."""

from datetime import datetime, timezone

import pytest

from project.application import commands
from project.application.command_handlers.create_event_reference_handler import (
    CreateEventReferenceHandler,
)
from project.application.command_handlers.delete_event_reference_handler import (
    DeleteEventReferenceHandler,
)
from project.application.command_handlers.update_event_reference_handler import (
    UpdateEventReferenceHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from tests.application.conftest import ACTOR, grant_permission


def _make_event(uow, admin_unit_id=2):
    event = EventAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Referenced Event",
        organizer_id=1,
        event_place_id=1,
        date_definitions=[
            EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
        ],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )
    uow.events.add(event)
    return event


# ---------------------------------------------------------------------------
# CreateEventReferenceHandler
# ---------------------------------------------------------------------------


class TestCreateEventReferenceHandler:
    def test_creates_reference_and_returns_result(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        grant_permission(uow, 1, "incoming_event_references:write")
        cmd = commands.CreateEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id, rating=50
        )

        result = CreateEventReferenceHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.event_references.get(result.id)
        assert created is not None
        assert created.admin_unit_id == 1
        assert created.event_id == event.id

    def test_own_event_raises_constraint_error(self, uow):
        event = _make_event(uow, admin_unit_id=1)
        grant_permission(uow, 1, "incoming_event_references:write")
        cmd = commands.CreateEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id, rating=50
        )

        with pytest.raises(ConstraintError):
            CreateEventReferenceHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        cmd = commands.CreateEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id, rating=50
        )

        with pytest.raises(UnauthorizedError):
            CreateEventReferenceHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateEventReferenceHandler
# ---------------------------------------------------------------------------


class TestUpdateEventReferenceHandler:
    def _seed(self, uow, admin_unit_id=1):
        reference = EventReferenceAggregate.create(
            actor=Actor(), admin_unit_id=admin_unit_id, event_id=1, rating=50
        )
        uow.event_references.add(reference)
        return reference

    def test_updates_reference(self, uow):
        reference = self._seed(uow)
        grant_permission(uow, 1, "incoming_event_references:write")
        cmd = commands.UpdateEventReferenceCommand.model_construct(
            actor=ACTOR, id=reference.id, rating=80
        )

        UpdateEventReferenceHandler().handle(cmd, uow)

        updated = uow.event_references.get(reference.id)
        assert updated.rating == 80

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateEventReferenceCommand.model_construct(
            actor=Actor(), id=9999, rating=80
        )

        with pytest.raises(NotFoundError):
            UpdateEventReferenceHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        reference = self._seed(uow)
        cmd = commands.UpdateEventReferenceCommand.model_construct(
            actor=ACTOR, id=reference.id, rating=80
        )

        with pytest.raises(UnauthorizedError):
            UpdateEventReferenceHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteEventReferenceHandler
# ---------------------------------------------------------------------------


class TestDeleteEventReferenceHandler:
    def _seed(self, uow, admin_unit_id=1):
        reference = EventReferenceAggregate.create(
            actor=Actor(), admin_unit_id=admin_unit_id, event_id=1, rating=50
        )
        uow.event_references.add(reference)
        return reference

    def test_removes_reference(self, uow):
        reference = self._seed(uow)
        reference_id = reference.id
        grant_permission(uow, 1, "incoming_event_references:write")

        cmd = commands.DeleteEventReferenceCommand.model_construct(
            actor=ACTOR, id=reference_id
        )
        DeleteEventReferenceHandler().handle(cmd, uow)

        assert uow.event_references.get(reference_id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteEventReferenceCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            DeleteEventReferenceHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        reference = self._seed(uow)
        cmd = commands.DeleteEventReferenceCommand.model_construct(
            actor=ACTOR, id=reference.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteEventReferenceHandler().handle(cmd, uow)
