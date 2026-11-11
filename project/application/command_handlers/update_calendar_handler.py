from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.types import unset

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .calendar_utils import ensure_calendar_exists, ensure_calendar_name_is_free


class UpdateCalendarHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateCalendarCommand, uow: AbstractUnitOfWork):
        calendar = ensure_calendar_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, calendar.admin_unit_id, "calendars:write", uow
        )
        if cmd.name != unset:
            ensure_calendar_name_is_free(
                calendar.admin_unit_id, cmd.name, uow, exclude_id=calendar.id
            )

        calendar.update(
            actor=cmd.actor,
            name=cmd.name,
            description=cmd.description,
            private=cmd.private,
        )
        uow.calendars.update(calendar)
