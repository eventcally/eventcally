"""Unit tests for event command handlers (Create, Update, Delete)."""

from datetime import datetime, timezone

import pytest

from project.application import commands
from project.application.command_handlers.create_event_handler import CreateEventHandler
from project.application.command_handlers.delete_event_handler import DeleteEventHandler
from project.application.command_handlers.update_event_handler import UpdateEventHandler
from project.domain.errors import NotFoundError
from project.domain.errors.constraint_error import ConstraintError
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from tests.application.conftest import FakeUnitOfWork

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_organizer(uow: FakeUnitOfWork, admin_unit_id=1):
    org = EventOrganizerAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Organizer",
    )
    uow.event_organizers.add(org)
    return org


def _make_place(uow: FakeUnitOfWork, admin_unit_id=1):
    place = EventPlaceAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Place",
    )
    uow.event_places.add(place)
    return place


def _date_def():
    return EventDateDefinitionValueObject(start=datetime.now(timezone.utc))


def _make_create_cmd(admin_unit_id, organizer_id, event_place_id, **kwargs):
    return commands.CreateEventCommand.model_construct(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Test Event",
        organizer_id=organizer_id,
        event_place_id=event_place_id,
        date_definitions=[_date_def()],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
        description=None,
        external_link=None,
        ticket_link=None,
        tags=None,
        internal_tags=None,
        kid_friendly=None,
        accessible_for_free=None,
        age_from=None,
        age_to=None,
        registration_required=None,
        booked_up=None,
        expected_participants=None,
        price_info=None,
        target_group_origin=None,
        attendance_mode=None,
        photo=None,
        previous_start_date=None,
        category_ids=None,
        custom_category_ids=None,
        rating=None,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# CreateEventHandler
# ---------------------------------------------------------------------------


class TestCreateEventHandler:
    def test_creates_event_and_returns_result(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        place = _make_place(uow, admin_unit_id=1)
        cmd = _make_create_cmd(1, org.id, place.id)

        result = CreateEventHandler().handle(cmd, uow)

        assert result.id is not None
        assert result.id > 0
        created = uow.events.get(result.id)
        assert created is not None
        assert created.name == "Test Event"

    def test_commits(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        place = _make_place(uow, admin_unit_id=1)
        cmd = _make_create_cmd(1, org.id, place.id)

        CreateEventHandler().handle(cmd, uow)

        assert uow.committed

    def test_organizer_wrong_admin_unit_raises_constraint_error(self, uow):
        org = _make_organizer(uow, admin_unit_id=2)  # different unit
        place = _make_place(uow, admin_unit_id=1)
        cmd = _make_create_cmd(1, org.id, place.id)

        with pytest.raises(ConstraintError):
            CreateEventHandler().handle(cmd, uow)

    def test_co_organizer_wrong_admin_unit_raises_constraint_error(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        co_org = _make_organizer(uow, admin_unit_id=2)  # different unit
        place = _make_place(uow, admin_unit_id=1)
        cmd = _make_create_cmd(1, org.id, place.id, co_organizer_ids=[co_org.id])

        with pytest.raises(ConstraintError):
            CreateEventHandler().handle(cmd, uow)

    def test_co_organizer_same_admin_unit_succeeds(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        co_org = _make_organizer(uow, admin_unit_id=1)
        place = _make_place(uow, admin_unit_id=1)
        cmd = _make_create_cmd(1, org.id, place.id, co_organizer_ids=[co_org.id])

        result = CreateEventHandler().handle(cmd, uow)
        assert result.id > 0

    def test_place_wrong_admin_unit_raises_constraint_error(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        place = _make_place(uow, admin_unit_id=2)  # different unit
        cmd = _make_create_cmd(1, org.id, place.id)

        with pytest.raises(ConstraintError):
            CreateEventHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# UpdateEventHandler
# ---------------------------------------------------------------------------


class TestUpdateEventHandler:
    def _seed_event(self, uow, admin_unit_id=1):
        org = _make_organizer(uow, admin_unit_id=admin_unit_id)
        place = _make_place(uow, admin_unit_id=admin_unit_id)
        event = EventAggregate.create(
            actor=Actor(),
            admin_unit_id=admin_unit_id,
            name="Original",
            organizer_id=org.id,
            event_place_id=place.id,
            date_definitions=[_date_def()],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        uow.events.add(event)
        return event, org, place

    def test_updates_event_and_commits(self, uow):
        event, _, _ = self._seed_event(uow)
        cmd = commands.UpdateEventCommand.model_construct(
            actor=Actor(),
            id=event.id,
        )

        UpdateEventHandler().handle(cmd, uow)

        assert uow.committed

    def test_event_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateEventCommand.model_construct(
            actor=Actor(),
            id=9999,
        )

        with pytest.raises(NotFoundError):
            UpdateEventHandler().handle(cmd, uow)

    def test_wrong_organizer_unit_raises_constraint_error(self, uow):
        event, _, _ = self._seed_event(uow, admin_unit_id=1)
        wrong_org = _make_organizer(uow, admin_unit_id=2)
        cmd = commands.UpdateEventCommand.model_construct(
            actor=Actor(),
            id=event.id,
            organizer_id=wrong_org.id,
        )

        with pytest.raises(ConstraintError):
            UpdateEventHandler().handle(cmd, uow)

    def test_wrong_co_organizer_unit_raises_constraint_error(self, uow):
        event, _, _ = self._seed_event(uow, admin_unit_id=1)
        wrong_co_org = _make_organizer(uow, admin_unit_id=2)
        cmd = commands.UpdateEventCommand.model_construct(
            actor=Actor(),
            id=event.id,
            co_organizer_ids=[wrong_co_org.id],
        )

        with pytest.raises(ConstraintError):
            UpdateEventHandler().handle(cmd, uow)

    def test_wrong_place_unit_raises_constraint_error(self, uow):
        event, _, _ = self._seed_event(uow, admin_unit_id=1)
        wrong_place = _make_place(uow, admin_unit_id=2)
        cmd = commands.UpdateEventCommand.model_construct(
            actor=Actor(),
            id=event.id,
            event_place_id=wrong_place.id,
        )

        with pytest.raises(ConstraintError):
            UpdateEventHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# DeleteEventHandler
# ---------------------------------------------------------------------------


class TestDeleteEventHandler:
    def test_removes_event_and_commits(self, uow):
        org = _make_organizer(uow, admin_unit_id=1)
        place = _make_place(uow, admin_unit_id=1)
        event = EventAggregate.create(
            actor=Actor(),
            admin_unit_id=1,
            name="To Delete",
            organizer_id=org.id,
            event_place_id=place.id,
            date_definitions=[_date_def()],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        uow.events.add(event)
        event_id = event.id

        cmd = commands.DeleteEventCommand.model_construct(actor=Actor(), id=event_id)
        DeleteEventHandler().handle(cmd, uow)

        assert uow.events.get(event_id) is None
        assert uow.committed

    def test_event_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteEventCommand.model_construct(actor=Actor(), id=9999)

        with pytest.raises(NotFoundError):
            DeleteEventHandler().handle(cmd, uow)
