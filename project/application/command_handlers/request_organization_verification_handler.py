from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class RequestOrganizationVerificationHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.RequestOrganizationVerificationCommand,
        uow: AbstractUnitOfWork,
    ):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            cmd.source_admin_unit_id,
            "outgoing_organization_verification_requests:write",
            uow,
        )

        verification_request = OrganizationVerificationRequestAggregate.create(
            actor=cmd.actor,
            source_admin_unit_id=cmd.source_admin_unit_id,
            target_admin_unit_id=cmd.target_admin_unit_id,
        )
        uow.organization_verification_requests.add(verification_request)

        return commands.RequestOrganizationVerificationCommandResult(
            id=verification_request.id
        )
