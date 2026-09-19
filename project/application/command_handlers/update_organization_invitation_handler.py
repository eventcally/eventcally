from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .invitation_utils import ensure_organization_invitation_exists


class UpdateOrganizationInvitationHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.UpdateOrganizationInvitationCommand,
        uow: AbstractUnitOfWork,
    ):
        organization_invitation = ensure_organization_invitation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            organization_invitation.admin_unit_id,
            "organization_invitations:write",
            uow,
        )

        organization_invitation.update(
            actor=cmd.actor,
            admin_unit_name=cmd.admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                cmd.relation_auto_verify_event_reference_requests
            ),
            relation_verify=cmd.relation_verify,
        )
        uow.organization_invitations.update(organization_invitation)
