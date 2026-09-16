from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .invitation_utils import (
    ensure_actor_is_invitation_receiver,
    ensure_organization_invitation_exists,
)


class DeclineOrganizationInvitationHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.DeclineOrganizationInvitationCommand,
        uow: AbstractUnitOfWork,
    ):
        organization_invitation = ensure_organization_invitation_exists(cmd.id, uow)

        ensure_actor_is_invitation_receiver(
            cmd.actor, organization_invitation.email, uow
        )

        organization_invitation.delete(cmd.actor)
        uow.organization_invitations.remove(organization_invitation)
