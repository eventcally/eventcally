from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_calendar_exists


class DeleteCalendarHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteCalendarCommand, uow: AbstractUnitOfWork):
        calendar = ensure_calendar_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, calendar.admin_unit_id, "calendars:write", uow
        )

        calendar.delete(cmd.actor)
        uow.calendars.remove(calendar)
