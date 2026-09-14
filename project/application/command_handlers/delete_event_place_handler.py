from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_place_utils import ensure_event_place_exists


class DeleteEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteEventPlaceCommand, uow: AbstractUnitOfWork):
        event_place = ensure_event_place_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, event_place.admin_unit_id, "event_places:write", uow
        )

        event_place.delete(cmd.actor)
        uow.event_places.remove(event_place)
