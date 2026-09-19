from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_member_utils import ensure_organization_member_exists


class RemoveOrganizationMemberHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RemoveOrganizationMemberCommand, uow: AbstractUnitOfWork
    ):
        member = ensure_organization_member_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, member.admin_unit_id, "organization_members:write", uow
        )

        uow.organization_members.remove(member)
