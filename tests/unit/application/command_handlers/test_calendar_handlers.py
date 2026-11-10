"""Unit tests for calendar command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.create_calendar_handler import (
    CreateCalendarHandler,
)
from project.application.command_handlers.delete_calendar_handler import (
    DeleteCalendarHandler,
)
from project.application.command_handlers.update_calendar_handler import (
    UpdateCalendarHandler,
)
from project.domain.errors import DuplicateError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.models.entities.actor import Actor
from tests.unit.application.conftest import ACTOR, grant_permission


def _seed(uow, name="Calendar", admin_unit_id=1):
    calendar = CalendarAggregate.create(
        actor=Actor(), admin_unit_id=admin_unit_id, name=name
    )
    uow.calendars.add(calendar)
    return calendar


class TestCreateCalendarHandler:
    def test_creates_calendar_and_returns_result(self, uow):
        grant_permission(uow, 1, "calendars:write")
        cmd = commands.CreateCalendarCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, name="Sports", description="d", private=True
        )

        result = CreateCalendarHandler().handle(cmd, uow)

        created = uow.calendars.get(result.id)
        assert created.name == "Sports"
        assert created.description == "d"
        assert created.private is True

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.CreateCalendarCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, name="Sports", description=None, private=False
        )

        with pytest.raises(UnauthorizedError):
            CreateCalendarHandler().handle(cmd, uow)

    def test_duplicate_name_raises_duplicate_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        _seed(uow, name="Sports")
        cmd = commands.CreateCalendarCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=1,
            name=" sports ",
            description=None,
            private=False,
        )

        with pytest.raises(DuplicateError):
            CreateCalendarHandler().handle(cmd, uow)

    def test_same_name_in_other_organization_is_allowed(self, uow):
        grant_permission(uow, 1, "calendars:write")
        _seed(uow, name="Sports", admin_unit_id=2)
        cmd = commands.CreateCalendarCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, name="Sports", description=None, private=False
        )

        assert CreateCalendarHandler().handle(cmd, uow).id > 0


class TestUpdateCalendarHandler:
    def test_updates_calendar(self, uow):
        calendar = _seed(uow)
        grant_permission(uow, 1, "calendars:write")
        cmd = commands.UpdateCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id, name="New", private=True
        )

        UpdateCalendarHandler().handle(cmd, uow)

        updated = uow.calendars.get(calendar.id)
        assert updated.name == "New"
        assert updated.private is True

    def test_keeping_the_own_name_is_allowed(self, uow):
        calendar = _seed(uow, name="Same")
        grant_permission(uow, 1, "calendars:write")
        cmd = commands.UpdateCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id, name="same"
        )

        UpdateCalendarHandler().handle(cmd, uow)

        assert uow.calendars.get(calendar.id).name == "same"

    def test_name_of_other_calendar_raises_duplicate_error(self, uow):
        _seed(uow, name="Taken")
        calendar = _seed(uow, name="Mine")
        grant_permission(uow, 1, "calendars:write")
        cmd = commands.UpdateCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id, name="Taken"
        )

        with pytest.raises(DuplicateError):
            UpdateCalendarHandler().handle(cmd, uow)

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateCalendarCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            UpdateCalendarHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        calendar = _seed(uow)
        cmd = commands.UpdateCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id, name="New"
        )

        with pytest.raises(UnauthorizedError):
            UpdateCalendarHandler().handle(cmd, uow)


class TestDeleteCalendarHandler:
    def test_removes_calendar(self, uow):
        calendar = _seed(uow)
        grant_permission(uow, 1, "calendars:write")
        cmd = commands.DeleteCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id
        )

        DeleteCalendarHandler().handle(cmd, uow)

        assert uow.calendars.get(calendar.id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.DeleteCalendarCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            DeleteCalendarHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        calendar = _seed(uow)
        cmd = commands.DeleteCalendarCommand.model_construct(
            actor=ACTOR, id=calendar.id
        )

        with pytest.raises(UnauthorizedError):
            DeleteCalendarHandler().handle(cmd, uow)
