from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_reference_utils import ensure_event_reference_exists


class UpdateEventReferenceHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateEventReferenceCommand, uow: AbstractUnitOfWork
    ):
        event_reference = ensure_event_reference_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            event_reference.admin_unit_id,
            "incoming_event_references:write",
            uow,
        )

        event_reference.update(
            actor=cmd.actor,
            rating=cmd.rating,
        )
        uow.event_references.update(event_reference)
