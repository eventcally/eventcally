from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .organization_relation_utils import (
    ensure_actor_can_verify_organization,
    verify_organization_relation,
)
from .organization_verification_request_utils import (
    ensure_organization_verification_request_exists,
)


class ApproveOrganizationVerificationRequestHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.ApproveOrganizationVerificationRequestCommand,
        uow: AbstractUnitOfWork,
    ):
        verification_request = ensure_organization_verification_request_exists(
            cmd.id, uow
        )

        # The request's target reviews (verifies) its source.
        ensure_actor_can_verify_organization(
            uow,
            cmd.actor,
            verification_request.target_admin_unit_id,
            verification_request.source_admin_unit_id,
        )

        verification_request.approve(cmd.actor)
        uow.organization_verification_requests.update(verification_request)

        # The resulting relation is the other way around: the verifier becomes
        # the relation's source, and the verified organization becomes its
        # target.
        relation = verify_organization_relation(
            uow,
            cmd.actor,
            verification_request.target_admin_unit_id,
            verification_request.source_admin_unit_id,
            cmd.auto_verify_event_reference_requests,
        )

        return commands.ApproveOrganizationVerificationRequestCommandResult(
            id=relation.id
        )
