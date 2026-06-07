from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .event_place_utils import ensure_event_place_exists


class UpdateEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateEventPlaceCommand, uow: AbstractUnitOfWork):
        with uow:
            event_place = ensure_event_place_exists(cmd.id, uow)
            event_place.update(
                actor=cmd.actor,
                name=cmd.name,
                url=cmd.url,
                description=cmd.description,
                location=cmd.location,
                photo=ImageEntity.from_nullable_unsetable_value_object(cmd.photo),
            )
            uow.event_places.update(event_place)
            uow.commit()
