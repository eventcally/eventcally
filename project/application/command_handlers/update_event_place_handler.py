from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_place_utils import ensure_event_place_exists


class UpdateEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateEventPlaceCommand, uow: AbstractUnitOfWork):
        event_place = ensure_event_place_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, event_place.admin_unit_id, "event_places:write", uow
        )

        event_place.update(
            actor=cmd.actor,
            name=cmd.name,
            url=cmd.url,
            description=cmd.description,
            location=cmd.location,
            photo=ImageEntity.from_nullable_unsetable_value_object(cmd.photo),
        )
        uow.event_places.update(event_place)
