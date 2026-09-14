from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_verification_request_utils import (
    ensure_organization_verification_request_exists,
)


class WithdrawOrganizationVerificationRequestHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.WithdrawOrganizationVerificationRequestCommand,
        uow: AbstractUnitOfWork,
    ):
        verification_request = ensure_organization_verification_request_exists(
            cmd.id, uow
        )

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            verification_request.source_admin_unit_id,
            "outgoing_organization_verification_requests:write",
            uow,
        )

        verification_request.delete(cmd.actor)
        uow.organization_verification_requests.remove(verification_request)
