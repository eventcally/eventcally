from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_member_utils import ensure_organization_member_exists


class ChangeOrganizationMemberRolesHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.ChangeOrganizationMemberRolesCommand,
        uow: AbstractUnitOfWork,
    ):
        member = ensure_organization_member_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, member.admin_unit_id, "organization_members:write", uow
        )

        roles = list(cmd.roles)
        if member.user_id == cmd.actor.user_id:
            actor_user = uow.users.get(cmd.actor.user_id)
            if not actor_user.is_platform_admin and "admin" not in roles:
                roles.append("admin")

        member.update(actor=cmd.actor, roles=roles)
        uow.organization_members.update(member)
