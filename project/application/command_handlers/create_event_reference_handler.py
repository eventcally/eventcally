from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors.constraint_error import ConstraintError
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)

from .abstract_command_handler import AbstractCommandHandler


class CreateEventReferenceHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CreateEventReferenceCommand, uow: AbstractUnitOfWork
    ):
        event = ensure_event_exists(cmd.event_id, uow)
        if event.admin_unit_id == cmd.admin_unit_id:
            raise ConstraintError("Own events cannot be referenced")

        event_reference = EventReferenceAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            event_id=cmd.event_id,
            rating=cmd.rating,
        )
        uow.event_references.add(event_reference)

        return commands.CreateEventReferenceCommandResult(id=event_reference.id)
