from project.application import commands
from project.application.services.abstract_oauth2_client_credentials_generator import (
    AbstractOAuth2ClientCredentialsGenerator,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .oauth2_client_utils import ensure_actor_can_manage_oauth2_client_owner


class CreateOAuth2ClientHandler(AbstractCommandHandler):
    def __init__(self, credentials_generator: AbstractOAuth2ClientCredentialsGenerator):
        super().__init__()
        self.credentials_generator = credentials_generator

    def handle(self, cmd: commands.CreateOAuth2ClientCommand, uow: AbstractUnitOfWork):
        ensure_actor_can_manage_oauth2_client_owner(
            cmd.actor, cmd.user_id, cmd.admin_unit_id, uow
        )

        client_id, client_secret = self.credentials_generator.generate()
        oauth2_client = OAuth2ClientAggregate.create(
            actor=cmd.actor,
            name=cmd.name,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=cmd.redirect_uris,
            scope=cmd.scope,
            user_id=cmd.user_id,
            admin_unit_id=cmd.admin_unit_id,
        )
        uow.oauth2_clients.add(oauth2_client)

        return commands.CreateOAuth2ClientCommandResult(
            id=oauth2_client.id,
            client_id=client_id,
            client_secret=client_secret,
        )
