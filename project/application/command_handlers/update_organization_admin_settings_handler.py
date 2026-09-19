from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin
from .organization_utils import ensure_organization_exists


class UpdateOrganizationAdminSettingsHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.UpdateOrganizationAdminSettingsCommand,
        uow: AbstractUnitOfWork,
    ):
        organization = ensure_organization_exists(cmd.id, uow)

        ensure_actor_is_platform_admin(cmd.actor, uow)

        organization.update(
            actor=cmd.actor,
            incoming_reference_requests_allowed=cmd.incoming_reference_requests_allowed,
            can_create_other=cmd.can_create_other,
            can_invite_other=cmd.can_invite_other,
            can_verify_other=cmd.can_verify_other,
        )
        uow.organizations.update(organization)
