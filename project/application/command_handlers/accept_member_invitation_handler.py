from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .invitation_utils import (
    ensure_actor_is_invitation_receiver,
    ensure_member_invitation_exists,
)


class AcceptMemberInvitationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.AcceptMemberInvitationCommand, uow: AbstractUnitOfWork
    ):
        member_invitation = ensure_member_invitation_exists(cmd.id, uow)

        ensure_actor_is_invitation_receiver(cmd.actor, member_invitation.email, uow)

        member = uow.organization_members.get_by_admin_unit_and_user(
            member_invitation.admin_unit_id, cmd.actor.user_id
        )
        if member is None:
            member = OrganisationMemberAggregate.create(
                admin_unit_id=member_invitation.admin_unit_id,
                user_id=cmd.actor.user_id,
                roles=member_invitation.roles,
            )
            uow.organization_members.add(member)
        else:
            member.add_roles(member_invitation.roles)
            uow.organization_members.update(member)

        uow.member_invitations.remove(member_invitation)
