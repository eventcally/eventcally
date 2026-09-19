from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_verification_request_utils import (
    ensure_organization_verification_request_exists,
)


class RejectOrganizationVerificationRequestHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.RejectOrganizationVerificationRequestCommand,
        uow: AbstractUnitOfWork,
    ):
        verification_request = ensure_organization_verification_request_exists(
            cmd.id, uow
        )

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            verification_request.target_admin_unit_id,
            "incoming_organization_verification_requests:write",
            uow,
        )

        verification_request.reject(cmd.actor, cmd.rejection_reason)
        uow.organization_verification_requests.update(verification_request)
