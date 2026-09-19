from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin
from .organization_utils import ensure_organization_exists


class DeleteOrganizationHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteOrganizationCommand, uow: AbstractUnitOfWork):
        organization = ensure_organization_exists(cmd.id, uow)

        ensure_actor_is_platform_admin(cmd.actor, uow)

        organization.delete(cmd.actor)
        uow.organizations.remove(organization)
