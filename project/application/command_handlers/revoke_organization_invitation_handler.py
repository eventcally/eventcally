from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .invitation_utils import ensure_organization_invitation_exists


class RevokeOrganizationInvitationHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.RevokeOrganizationInvitationCommand,
        uow: AbstractUnitOfWork,
    ):
        organization_invitation = ensure_organization_invitation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            organization_invitation.admin_unit_id,
            "organization_invitations:write",
            uow,
        )

        organization_invitation.delete(cmd.actor)
        uow.organization_invitations.remove(organization_invitation)
