from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteOldWebhookEventsHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteOldWebhookEventsCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            deleted_count = uow.webhooks.delete_old_events(days=3)
            uow.commit()
            return deleted_count
