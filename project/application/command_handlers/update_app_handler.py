from project.application import commands
from project.application.command_handlers.app_utils import ensure_app_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class UpdateAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app = ensure_app_exists(cmd.id, uow)
            app.update(
                actor=cmd.actor,
                name=cmd.name,
                description=cmd.description,
                homepage_url=cmd.homepage_url,
                setup_url=cmd.setup_url,
                webhook=cmd.webhook,
            )
            uow.apps.update(app)
            uow.commit()
