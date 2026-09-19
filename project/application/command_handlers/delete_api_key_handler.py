from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .api_key_utils import ensure_actor_can_manage_api_key_owner, ensure_api_key_exists


class DeleteApiKeyHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteApiKeyCommand, uow: AbstractUnitOfWork):
        api_key = ensure_api_key_exists(cmd.id, uow)

        ensure_actor_can_manage_api_key_owner(
            cmd.actor, api_key.user_id, api_key.admin_unit_id, uow
        )

        api_key.delete(cmd.actor)
        uow.api_keys.remove(api_key)
