from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.translation import dummy_gettext

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_calendar_exists


class RemoveEventFromCalendarHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RemoveEventFromCalendarCommand, uow: AbstractUnitOfWork
    ):
        calendar = ensure_calendar_exists(cmd.calendar_id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, calendar.admin_unit_id, "calendars:write", uow
        )

        entry = uow.calendar_entries.get_by_calendar_and_event(
            calendar.id, cmd.event_id
        )
        if not entry:
            raise NotFoundError(dummy_gettext("The event is not in this calendar"))

        entry.delete(cmd.actor)
        uow.calendar_entries.remove(entry)
