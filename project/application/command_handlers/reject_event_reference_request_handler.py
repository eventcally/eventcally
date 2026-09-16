from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_reference_request_utils import ensure_event_reference_request_exists
from .organization_relation_utils import get_or_create_organization_relation


class RejectEventReferenceRequestHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.RejectEventReferenceRequestCommand,
        uow: AbstractUnitOfWork,
    ):
        event_reference_request = ensure_event_reference_request_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            event_reference_request.admin_unit_id,
            "incoming_event_reference_requests:write",
            uow,
        )

        event_reference_request.reject(cmd.actor, cmd.rejection_reason)
        uow.event_reference_requests.update(event_reference_request)

        if cmd.auto_verify:
            event = uow.events.get(event_reference_request.event_id)
            get_or_create_organization_relation(
                uow,
                cmd.actor,
                source_admin_unit_id=event_reference_request.admin_unit_id,
                target_admin_unit_id=event.admin_unit_id,
                auto_verify_event_reference_requests=True,
            )
