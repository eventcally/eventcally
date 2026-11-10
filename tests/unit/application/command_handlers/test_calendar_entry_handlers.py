"""Unit tests for the calendar entry command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.add_event_to_calendar_handler import (
    AddEventToCalendarHandler,
)
from project.application.command_handlers.remove_event_from_calendar_handler import (
    RemoveEventFromCalendarHandler,
)
from project.application.command_handlers.set_event_calendars_handler import (
    SetEventCalendarsHandler,
)
from project.domain.errors import (
    ConstraintError,
    DuplicateError,
    NotFoundError,
    UnauthorizedError,
)
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from tests.unit.application.conftest import ACTOR, grant_permission


def _calendar(uow, admin_unit_id=1, name="Calendar"):
    calendar = CalendarAggregate.create(
        actor=Actor(), admin_unit_id=admin_unit_id, name=name
    )
    uow.calendars.add(calendar)
    return calendar


def _event(uow, admin_unit_id=1, public_status=EventPublicStatus.published):
    event = EventAggregate.model_construct(
        id=-1, admin_unit_id=admin_unit_id, public_status=public_status
    )
    uow.events.add(event)
    return event


def _entries(uow):
    return {(e.calendar_id, e.event_id) for e in uow.calendar_entries._store.values()}


class TestAddEventToCalendarHandler:
    def _cmd(self, calendar, event):
        return commands.AddEventToCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=calendar.id, event_id=event.id
        )

    def test_adds_own_draft_event(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow, public_status=EventPublicStatus.draft)

        result = AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

        assert result.id > 0
        assert _entries(uow) == {(calendar.id, event.id)}

    @pytest.mark.parametrize(
        "status", [EventPublicStatus.published, EventPublicStatus.planned]
    )
    def test_adds_foreign_published_or_planned_event(self, uow, status):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow, admin_unit_id=2, public_status=status)

        AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

        assert _entries(uow) == {(calendar.id, event.id)}

    def test_foreign_draft_event_raises_constraint_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow, admin_unit_id=2, public_status=EventPublicStatus.draft)

        with pytest.raises(ConstraintError):
            AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

    def test_duplicate_raises_duplicate_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow)
        AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

        with pytest.raises(DuplicateError):
            AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

    def test_unknown_calendar_raises_not_found_error(self, uow):
        event = _event(uow)
        cmd = commands.AddEventToCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=99, event_id=event.id
        )

        with pytest.raises(NotFoundError):
            AddEventToCalendarHandler().handle(cmd, uow)

    def test_without_permission_raises_unauthorized_error(self, uow):
        calendar = _calendar(uow)
        event = _event(uow)

        with pytest.raises(UnauthorizedError):
            AddEventToCalendarHandler().handle(self._cmd(calendar, event), uow)

    def test_unknown_event_raises_not_found_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        cmd = commands.AddEventToCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=calendar.id, event_id=99
        )

        with pytest.raises(NotFoundError):
            AddEventToCalendarHandler().handle(cmd, uow)


class TestRemoveEventFromCalendarHandler:
    def test_removes_entry(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow)
        uow.calendar_entries.add(
            CalendarEntryAggregate.create(Actor(), calendar.id, event.id)
        )
        cmd = commands.RemoveEventFromCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=calendar.id, event_id=event.id
        )

        RemoveEventFromCalendarHandler().handle(cmd, uow)

        assert _entries(uow) == set()

    def test_missing_entry_raises_not_found_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        cmd = commands.RemoveEventFromCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=calendar.id, event_id=5
        )

        with pytest.raises(NotFoundError):
            RemoveEventFromCalendarHandler().handle(cmd, uow)

    def test_unknown_calendar_raises_not_found_error(self, uow):
        cmd = commands.RemoveEventFromCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=99, event_id=5
        )

        with pytest.raises(NotFoundError):
            RemoveEventFromCalendarHandler().handle(cmd, uow)

    def test_without_permission_raises_unauthorized_error(self, uow):
        calendar = _calendar(uow)
        cmd = commands.RemoveEventFromCalendarCommand.model_construct(
            actor=ACTOR, calendar_id=calendar.id, event_id=5
        )

        with pytest.raises(UnauthorizedError):
            RemoveEventFromCalendarHandler().handle(cmd, uow)


class TestSetEventCalendarsHandler:
    def _cmd(self, event, calendar_ids, admin_unit_id=1):
        return commands.SetEventCalendarsCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=admin_unit_id,
            event_id=event.id,
            calendar_ids=calendar_ids,
        )

    def test_adds_and_removes_only_own_organization_entries(self, uow):
        grant_permission(uow, 1, "calendars:write")
        keep, drop, add = (_calendar(uow, name=n) for n in ("keep", "drop", "add"))
        foreign = _calendar(uow, admin_unit_id=2, name="foreign")
        event = _event(uow)
        for calendar in (keep, drop, foreign):
            uow.calendar_entries.add(
                CalendarEntryAggregate.create(Actor(), calendar.id, event.id)
            )

        SetEventCalendarsHandler().handle(self._cmd(event, [keep.id, add.id]), uow)

        assert _entries(uow) == {
            (keep.id, event.id),
            (add.id, event.id),
            (foreign.id, event.id),
        }

    def test_is_idempotent(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow)
        cmd = self._cmd(event, [calendar.id, calendar.id])

        SetEventCalendarsHandler().handle(cmd, uow)
        SetEventCalendarsHandler().handle(cmd, uow)

        assert _entries(uow) == {(calendar.id, event.id)}

    def test_calendar_of_other_organization_raises_not_found_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        foreign = _calendar(uow, admin_unit_id=2)
        event = _event(uow)

        with pytest.raises(NotFoundError):
            SetEventCalendarsHandler().handle(self._cmd(event, [foreign.id]), uow)

    def test_unknown_calendar_raises_not_found_error(self, uow):
        grant_permission(uow, 1, "calendars:write")
        event = _event(uow)

        with pytest.raises(NotFoundError):
            SetEventCalendarsHandler().handle(self._cmd(event, [99]), uow)

    def test_foreign_draft_event_cannot_be_added_but_removed(self, uow):
        grant_permission(uow, 1, "calendars:write")
        calendar = _calendar(uow)
        event = _event(uow, admin_unit_id=2, public_status=EventPublicStatus.draft)

        with pytest.raises(ConstraintError):
            SetEventCalendarsHandler().handle(self._cmd(event, [calendar.id]), uow)

        uow.calendar_entries.add(
            CalendarEntryAggregate.create(Actor(), calendar.id, event.id)
        )
        SetEventCalendarsHandler().handle(self._cmd(event, []), uow)
        assert _entries(uow) == set()

    def test_without_permission_raises_unauthorized_error(self, uow):
        event = _event(uow)

        with pytest.raises(UnauthorizedError):
            SetEventCalendarsHandler().handle(self._cmd(event, []), uow)
