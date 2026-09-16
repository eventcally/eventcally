from project.application import commands
from project.application.services.abstract_api_key_generator import (
    AbstractApiKeyGenerator,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import ConstraintError
from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate

from .abstract_command_handler import AbstractCommandHandler
from .api_key_utils import ensure_actor_can_manage_api_key_owner


class CreateApiKeyHandler(AbstractCommandHandler):
    def __init__(self, api_key_generator: AbstractApiKeyGenerator):
        super().__init__()
        self.api_key_generator = api_key_generator

    def handle(self, cmd: commands.CreateApiKeyCommand, uow: AbstractUnitOfWork):
        ensure_actor_can_manage_api_key_owner(
            cmd.actor, cmd.user_id, cmd.admin_unit_id, uow
        )

        count = uow.api_keys.count_for_owner(cmd.user_id, cmd.admin_unit_id)
        max_api_keys = (
            uow.users.get(cmd.user_id).max_api_keys
            if cmd.user_id is not None
            else uow.organizations.get(cmd.admin_unit_id).max_api_keys
        )
        if count >= max_api_keys:
            raise ConstraintError("The maximum number of API keys has been reached.")

        key, key_hash = self.api_key_generator.generate()
        api_key = ApiKeyAggregate.create(
            actor=cmd.actor,
            name=cmd.name,
            key_hash=key_hash,
            user_id=cmd.user_id,
            admin_unit_id=cmd.admin_unit_id,
        )
        uow.api_keys.add(api_key)

        return commands.CreateApiKeyCommandResult(id=api_key.id, key=key)
