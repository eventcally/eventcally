from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class CreateEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateEventPlaceCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "event_places:write", uow
        )

        event_place = EventPlaceAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            name=cmd.name,
            url=cmd.url,
            description=cmd.description,
            location=cmd.location,
            photo=ImageEntity.from_value_object(cmd.photo) if cmd.photo else None,
        )
        uow.event_places.add(event_place)

        return commands.CreateEventPlaceCommandResult(id=event_place.id)
