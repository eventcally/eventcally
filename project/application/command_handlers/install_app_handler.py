from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .app_utils import ensure_app_exists
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class InstallAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.InstallAppCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "app_installations:write", uow
        )

        app = ensure_app_exists(cmd.app_id, uow)
        app_installation = OrganisationAppInstallationAggregate.create(
            cmd.actor, cmd.admin_unit_id, cmd.app_id, app.app_permissions
        )
        uow.organization_app_installations.add(app_installation)

        return commands.InstallAppCommandResult(id=app_installation.id)
