from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.translation import dummy_gettext

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_event_may_be_added


class SetEventCalendarsHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.SetEventCalendarsCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "calendars:write", uow
        )

        wanted_ids = set(cmd.calendar_ids)
        for calendar_id in wanted_ids:
            calendar = uow.calendars.get(calendar_id)
            if not calendar or calendar.admin_unit_id != cmd.admin_unit_id:
                raise NotFoundError(dummy_gettext("Calendar not found"))

        event = ensure_event_exists(cmd.event_id, uow)

        current = {
            entry.calendar_id: entry
            for entry in uow.calendar_entries.get_by_event_and_admin_unit(
                event.id, cmd.admin_unit_id
            )
        }

        for calendar_id, entry in current.items():
            if calendar_id not in wanted_ids:
                entry.delete(cmd.actor)
                uow.calendar_entries.remove(entry)

        for calendar_id in sorted(wanted_ids - set(current)):
            ensure_event_may_be_added(event, cmd.admin_unit_id)
            uow.calendar_entries.add(
                CalendarEntryAggregate.create(
                    actor=cmd.actor, calendar_id=calendar_id, event_id=event.id
                )
            )
