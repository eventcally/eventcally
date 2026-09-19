from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_organizer_utils import ensure_event_organizer_exists


class DeleteEventOrganizerHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteEventOrganizerCommand, uow: AbstractUnitOfWork
    ):
        event_organizer = ensure_event_organizer_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, event_organizer.admin_unit_id, "event_organizers:write", uow
        )

        event_organizer.delete(cmd.actor)
        uow.event_organizers.remove(event_organizer)
