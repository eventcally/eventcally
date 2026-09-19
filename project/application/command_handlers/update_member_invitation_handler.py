from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .invitation_utils import ensure_member_invitation_exists


class UpdateMemberInvitationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateMemberInvitationCommand, uow: AbstractUnitOfWork
    ):
        member_invitation = ensure_member_invitation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            member_invitation.admin_unit_id,
            "organization_member_invitations:write",
            uow,
        )

        member_invitation.update(actor=cmd.actor, roles=cmd.roles)
        uow.member_invitations.update(member_invitation)
