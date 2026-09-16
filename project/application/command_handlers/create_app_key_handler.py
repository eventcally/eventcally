from project.application import commands
from project.application.services.abstract_app_key_generator import (
    AbstractAppKeyGenerator,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class CreateAppKeyHandler(AbstractCommandHandler):
    def __init__(self, app_key_generator: AbstractAppKeyGenerator):
        super().__init__()
        self.app_key_generator = app_key_generator

    def handle(self, cmd: commands.CreateAppKeyCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "app_keys:write", uow
        )

        checksum, kid, public_key, private_pem = self.app_key_generator.generate()
        app_key = AppKeyAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            app_id=cmd.app_id,
            checksum=checksum,
            kid=kid,
            public_key=public_key,
        )
        uow.app_keys.add(app_key)

        return commands.CreateAppKeyCommandResult(
            id=app_key.id, private_pem=private_pem
        )
