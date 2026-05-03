from __future__ import annotations

import logging
from typing import Union

from dependency_injector.errors import NoSuchProviderError

from project.context import ContextProvider
from project.domain import commands, events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.service_layer.abstract_command_dispatcher import AbstractCommandDispatcher
from project.service_layer.abstract_event_dispatcher import AbstractEventDispatcher

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


class MessageBus:
    def __init__(
        self,
        uow_factory,
        context_provider: ContextProvider,
        command_handler_factory,
        event_handler_factory,
        event_dispatcher: AbstractEventDispatcher,
        command_dispatcher: AbstractCommandDispatcher,
    ):
        self.uow_factory = uow_factory
        self.context_provider = context_provider
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
        try:
            handlers = self.event_handler_factory(type(event))
        except NoSuchProviderError:  # pragma: no cover
            return

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
            command.model_validate(command.model_dump())
            handler = self.command_handler_factory(type(command))
            result = handler.handle(command, uow)
            return result
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    def _set_missing_command_fields(self, command):
        if not hasattr(command, "actor"):
            command.actor = self.context_provider.current_actor
