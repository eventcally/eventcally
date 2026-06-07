from __future__ import annotations

import logging
from typing import Union

from project.application import commands
from project.application.abstract_command_dispatcher import AbstractCommandDispatcher
from project.application.abstract_command_handler_factory import (
    AbstractCommandHandlerFactory,
)
from project.application.abstract_event_dispatcher import AbstractEventDispatcher
from project.application.abstract_event_handler_factory import (
    AbstractEventHandlerFactory,
)
from project.application.services.abstract_app_context_provider import (
    AbstractAppContextProvider,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


class MessageBus:
    def __init__(
        self,
        uow_factory,
        app_context_provider: AbstractAppContextProvider,
        command_handler_factory: AbstractCommandHandlerFactory,
        event_handler_factory: AbstractEventHandlerFactory,
        event_dispatcher: AbstractEventDispatcher,
        command_dispatcher: AbstractCommandDispatcher,
    ):
        self.uow_factory = uow_factory
        self.app_context_provider = app_context_provider
        self.command_handler_factory = command_handler_factory
        self.event_handler_factory = event_handler_factory
        self.event_dispatcher = event_dispatcher
        self.command_dispatcher = command_dispatcher

    def create_uow(self) -> AbstractUnitOfWork:
        return self.uow_factory.uow()

    def handle(self, message: Message):
        uow = self.create_uow()
        result = None

        if isinstance(message, events.Event):
            self._handle_event(message, uow)
        elif isinstance(message, commands.Command):
            result = self._handle_command(message, uow)
        else:  # pragma: no cover
            raise Exception(f"{message} was not an Event or Command")

        for event in uow.collect_pending_events():
            self._dispatch_event(event)

        return result

    def handle_command(
        self, command: commands.CommandWithResult[commands.CommandResultType]
    ) -> commands.CommandResultType:
        return self.handle(command)

    def dispatch_command(self, command: commands.Command):
        self._set_missing_command_fields(command)
        self.command_dispatcher.dispatch(command)
        logger.debug(f"Dispatched {command.__class__.__name__}")

    def _dispatch_event(self, event: events.Event):
        self.event_dispatcher.dispatch(event)
        logger.debug(f"Dispatched {event.__class__.__name__}")

    def _handle_event(self, event: events.Event, uow: AbstractUnitOfWork):
        handlers = self.event_handler_factory(type(event))

        for handler in handlers:
            try:
                logger.debug("handling event %s with handler %s", event, handler)
                handler.handle(event, uow)
            except Exception:  # pragma: no cover
                logger.exception("Exception handling event %s", event)
                continue

    def _handle_command(self, command: commands.Command, uow: AbstractUnitOfWork):
        logger.debug("handling command %s", command)
        self._set_missing_command_fields(command)

        try:
            command_type = type(command)
            validated_command = command_type.model_validate(
                command.model_dump(round_trip=True), strict=True
            )
            handler = self.command_handler_factory(command_type)
            result = handler.handle(validated_command, uow)
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    def _set_missing_command_fields(self, command):
        if not hasattr(command, "actor"):
            command.actor = self.app_context_provider.get_current_actor()
