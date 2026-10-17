from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class UpdateEventRecurringDatesHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateEventRecurringDatesCommand, uow: AbstractUnitOfWork
    ) -> bool:
        """Returns whether the dates changed. Like the batch job it replaces, this
        writes the dates silently: no domain event, so no webhook per event."""
        event = ensure_event_exists(cmd.event_id, uow)

        if not event.update_event_dates_with_recurrence_rule():
            return False

        uow.events.update(event)
        return True
