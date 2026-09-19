from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class DeleteEventHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteEventCommand, uow: AbstractUnitOfWork):
        event = ensure_event_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, event.admin_unit_id, "events:write", uow
        )

        event.delete(cmd.actor)
        uow.events.remove(event)
