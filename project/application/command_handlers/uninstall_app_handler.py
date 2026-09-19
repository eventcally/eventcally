from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class UninstallAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UninstallAppCommand, uow: AbstractUnitOfWork):
        app_installation = uow.organization_app_installations.get(cmd.id)

        if not app_installation:
            raise NotFoundError(f"App installation with id {cmd.id} not found")

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, app_installation.admin_unit_id, "app_installations:write", uow
        )

        app_installation.delete(cmd.actor)
        uow.organization_app_installations.remove(app_installation)
