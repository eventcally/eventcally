from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_user
from .oauth2_token_utils import ensure_oauth2_token_exists


class RevokeOAuth2TokenHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.RevokeOAuth2TokenCommand, uow: AbstractUnitOfWork):
        oauth2_token = ensure_oauth2_token_exists(cmd.id, uow)

        ensure_actor_is_user(cmd.actor, oauth2_token.user_id)

        oauth2_token.revoke(cmd.actor)
        uow.oauth2_tokens.update(oauth2_token)
