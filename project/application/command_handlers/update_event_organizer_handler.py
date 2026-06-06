from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler
from .event_organizer_utils import ensure_event_organizer_exists


class UpdateEventOrganizerHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateEventOrganizerCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            event_organizer = ensure_event_organizer_exists(cmd.id, uow)
            event_organizer.update(
                actor=cmd.actor,
                name=cmd.name,
                url=cmd.url,
                email=cmd.email,
                phone=cmd.phone,
                fax=cmd.fax,
                location=cmd.location,
                logo=ImageEntity.from_nullable_unsetable_value_object(cmd.logo),
            )
            uow.event_organizers.update(event_organizer)
            uow.commit()
