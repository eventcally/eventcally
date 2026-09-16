from project.application import commands
from project.application.services.abstract_oauth2_client_credentials_generator import (
    AbstractOAuth2ClientCredentialsGenerator,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.app_aggregate import AppAggregate

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class CreateAppHandler(AbstractCommandHandler):
    def __init__(self, credentials_generator: AbstractOAuth2ClientCredentialsGenerator):
        super().__init__()
        self.credentials_generator = credentials_generator

    def handle(self, cmd: commands.CreateAppCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "apps:write", uow
        )

        client_id, client_secret = self.credentials_generator.generate()
        app = AppAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            name=cmd.name,
            app_permissions=cmd.app_permissions,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=cmd.redirect_uris,
            scope=cmd.scope,
            description=cmd.description,
            homepage_url=cmd.homepage_url,
            setup_url=cmd.setup_url,
            webhook=cmd.webhook,
        )
        uow.apps.add(app)

        return commands.CreateAppCommandResult(id=app.id)
