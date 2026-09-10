from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .event_reference_utils import ensure_event_reference_exists


class UpdateEventReferenceHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateEventReferenceCommand, uow: AbstractUnitOfWork
    ):
        event_reference = ensure_event_reference_exists(cmd.id, uow)
        event_reference.update(
            actor=cmd.actor,
            rating=cmd.rating,
        )
        uow.event_references.update(event_reference)
