from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import DuplicateError
from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.translation import dummy_gettext

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_calendar_exists, ensure_event_may_be_added


class AddEventToCalendarHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.AddEventToCalendarCommand, uow: AbstractUnitOfWork):
        calendar = ensure_calendar_exists(cmd.calendar_id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, calendar.admin_unit_id, "calendars:write", uow
        )

        event = ensure_event_exists(cmd.event_id, uow)
        ensure_event_may_be_added(event, calendar.admin_unit_id)

        if uow.calendar_entries.get_by_calendar_and_event(calendar.id, event.id):
            raise DuplicateError(dummy_gettext("The event is already in this calendar"))

        entry = CalendarEntryAggregate.create(
            actor=cmd.actor, calendar_id=calendar.id, event_id=event.id
        )
        uow.calendar_entries.add(entry)

        return commands.AddEventToCalendarCommandResult(id=entry.id)
