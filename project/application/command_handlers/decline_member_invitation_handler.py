from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .invitation_utils import (
    ensure_actor_is_invitation_receiver,
    ensure_member_invitation_exists,
)


class DeclineMemberInvitationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeclineMemberInvitationCommand, uow: AbstractUnitOfWork
    ):
        member_invitation = ensure_member_invitation_exists(cmd.id, uow)

        ensure_actor_is_invitation_receiver(cmd.actor, member_invitation.email, uow)

        member_invitation.delete(cmd.actor)
        uow.member_invitations.remove(member_invitation)
