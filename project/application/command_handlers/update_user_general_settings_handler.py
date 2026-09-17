from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_user
from .user_utils import ensure_user_exists


class UpdateUserGeneralSettingsHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateUserGeneralSettingsCommand, uow: AbstractUnitOfWork
    ):
        user = ensure_user_exists(cmd.id, uow)

        ensure_actor_is_user(cmd.actor, user.id)

        user.update(actor=cmd.actor, locale=cmd.locale)
        uow.users.update(user)
