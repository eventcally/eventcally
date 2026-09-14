from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_utils import ensure_organization_exists


class RequestOrganizationDeletionHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.RequestOrganizationDeletionCommand, uow: AbstractUnitOfWork
    ):
        organization = ensure_organization_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, organization.id, "settings:write", uow
        )

        organization.request_deletion(cmd.actor)
        uow.organizations.update(organization)
