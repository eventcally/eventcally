from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class InviteOrganizationHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.InviteOrganizationCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "organization_invitations:write", uow
        )

        organization_invitation = AdminUnitInvitationAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            email=cmd.email,
            admin_unit_name=cmd.admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                cmd.relation_auto_verify_event_reference_requests
            ),
            relation_verify=cmd.relation_verify,
        )
        uow.organization_invitations.add(organization_invitation)

        return commands.InviteOrganizationCommandResult(id=organization_invitation.id)
