from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .invitation_utils import ensure_member_invitation_exists


class RevokeMemberInvitationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RevokeMemberInvitationCommand, uow: AbstractUnitOfWork
    ):
        member_invitation = ensure_member_invitation_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            member_invitation.admin_unit_id,
            "organization_member_invitations:write",
            uow,
        )

        member_invitation.delete(cmd.actor)
        uow.member_invitations.remove(member_invitation)
