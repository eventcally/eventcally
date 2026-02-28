import logging

from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class LogEventHandler(AbstractEventHandler):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger

    def handle(self, event: events.Event, uow: AbstractUnitOfWork):
        self.logger.info(event.model_dump_json())
