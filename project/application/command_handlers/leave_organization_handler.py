from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import ConstraintError

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_user
from .organization_member_utils import ensure_organization_member_exists


class LeaveOrganizationHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.LeaveOrganizationCommand, uow: AbstractUnitOfWork):
        member = ensure_organization_member_exists(cmd.id, uow)

        ensure_actor_is_user(cmd.actor, member.user_id)

        actor_user = uow.users.get(cmd.actor.user_id)
        if not actor_user.is_platform_admin:
            other_admins = [
                m
                for m in uow.organization_members.get_all_with_permission(
                    member.admin_unit_id, "organization_members:write"
                )
                if m.user_id != member.user_id
            ]
            if not other_admins:
                raise ConstraintError(
                    "The last remaining administrator can not leave the organization."
                )

        uow.organization_members.remove(member)
