from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_calendar_name_is_free


class CreateCalendarHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateCalendarCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "calendars:write", uow
        )
        ensure_calendar_name_is_free(cmd.admin_unit_id, cmd.name, uow)

        calendar = CalendarAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            name=cmd.name,
            description=cmd.description,
            private=cmd.private,
        )
        uow.calendars.add(calendar)

        return commands.CreateCalendarCommandResult(id=calendar.id)
