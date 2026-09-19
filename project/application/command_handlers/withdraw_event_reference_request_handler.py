from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_reference_request_utils import ensure_event_reference_request_exists
from .event_utils import ensure_event_exists


class WithdrawEventReferenceRequestHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.WithdrawEventReferenceRequestCommand,
        uow: AbstractUnitOfWork,
    ):
        event_reference_request = ensure_event_reference_request_exists(cmd.id, uow)
        event = ensure_event_exists(event_reference_request.event_id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            event.admin_unit_id,
            "outgoing_event_reference_requests:write",
            uow,
        )

        event_reference_request.delete(cmd.actor)
        uow.event_reference_requests.remove(event_reference_request)
