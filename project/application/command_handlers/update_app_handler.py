from project.application import commands
from project.application.command_handlers.app_utils import ensure_app_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class UpdateAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateAppCommand, uow: AbstractUnitOfWork):
        app = ensure_app_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, app.admin_unit_id, "apps:write", uow
        )

        app.update(
            actor=cmd.actor,
            name=cmd.name,
            app_permissions=cmd.app_permissions,
            redirect_uris=cmd.redirect_uris,
            description=cmd.description,
            homepage_url=cmd.homepage_url,
            setup_url=cmd.setup_url,
            webhook=cmd.webhook,
        )
        uow.apps.update(app)
