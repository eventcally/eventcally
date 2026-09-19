from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class InviteUserToOrganizationHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.InviteUserToOrganizationCommand, uow: AbstractUnitOfWork
    ):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor,
            cmd.admin_unit_id,
            "organization_member_invitations:write",
            uow,
        )

        member_invitation = AdminUnitMemberInvitationAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            email=cmd.email,
            roles=cmd.roles,
        )
        uow.member_invitations.add(member_invitation)

        return commands.InviteUserToOrganizationCommandResult(id=member_invitation.id)
