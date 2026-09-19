from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .organization_relation_utils import (
    ensure_actor_can_verify_organization,
    verify_organization_relation,
)


class VerifyOrganizationHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.VerifyOrganizationCommand, uow: AbstractUnitOfWork):
        ensure_actor_can_verify_organization(
            uow,
            cmd.actor,
            cmd.source_admin_unit_id,
            cmd.target_admin_unit_id,
        )

        relation = verify_organization_relation(
            uow,
            cmd.actor,
            cmd.source_admin_unit_id,
            cmd.target_admin_unit_id,
            cmd.auto_verify_event_reference_requests,
        )

        return commands.VerifyOrganizationCommandResult(id=relation.id)
