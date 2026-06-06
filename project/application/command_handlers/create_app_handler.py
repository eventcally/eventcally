from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.app_aggregate import AppAggregate

from .abstract_command_handler import AbstractCommandHandler


class CreateAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app = AppAggregate.create(
                actor=cmd.actor,
                admin_unit_id=cmd.admin_unit_id,
                name=cmd.name,
                app_permissions=cmd.app_permissions,
                redirect_uris=cmd.redirect_uris,
                scope=cmd.scope,
                description=cmd.description,
                homepage_url=cmd.homepage_url,
                setup_url=cmd.setup_url,
                webhook=cmd.webhook,
            )
            uow.apps.add(app)
            uow.commit()

            return commands.CreateAppCommandResult(id=app.id)
