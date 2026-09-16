from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import ConstraintError
from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.domain.models.enums.event_public_status import EventPublicStatus

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .event_reference_request_utils import create_event_reference_for_request
from .event_utils import ensure_event_exists


class RequestEventReferenceHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RequestEventReferenceCommand, uow: AbstractUnitOfWork
    ) -> commands.RequestEventReferenceCommandResult:
        event = ensure_event_exists(cmd.event_id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            event.admin_unit_id,
            "outgoing_event_reference_requests:write",
            uow,
        )

        if event.public_status != EventPublicStatus.published:
            raise ConstraintError("Only published events can be referenced")

        relation = uow.organization_relations.get_by_source_and_target(
            cmd.admin_unit_id, event.admin_unit_id
        )
        auto_verify = bool(relation and relation.auto_verify_event_reference_requests)

        event_reference_request = EventReferenceRequestAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            event_id=cmd.event_id,
            auto_verified=auto_verify,
        )
        uow.event_reference_requests.add(event_reference_request)

        if auto_verify:
            create_event_reference_for_request(uow, cmd.actor, event_reference_request)

        return commands.RequestEventReferenceCommandResult(
            id=event_reference_request.id, verified=auto_verify
        )
