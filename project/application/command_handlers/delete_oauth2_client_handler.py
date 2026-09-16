from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .oauth2_client_utils import (
    ensure_actor_can_manage_oauth2_client_owner,
    ensure_oauth2_client_exists,
)


class DeleteOAuth2ClientHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteOAuth2ClientCommand, uow: AbstractUnitOfWork):
        oauth2_client = ensure_oauth2_client_exists(cmd.id, uow)

        ensure_actor_can_manage_oauth2_client_owner(
            cmd.actor, oauth2_client.user_id, oauth2_client.admin_unit_id, uow
        )

        oauth2_client.delete(cmd.actor)
        uow.oauth2_clients.remove(oauth2_client)
