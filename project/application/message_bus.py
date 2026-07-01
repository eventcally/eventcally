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
        result = None

        if isinstance(message, events.Event):
            self._handle_event(message)
        elif isinstance(message, commands.Command):
            result = self._handle_command(message)
        else:  # pragma: no cover
            raise Exception(f"{message} was not an Event or Command")

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
        logger.debug("dispatching event %r", event)

        try:
            event.validate_self()
            self.event_dispatcher.dispatch(event)
        except Exception:  # pragma: no cover
            logger.exception("Exception dispatching event %r", event)

    def _handle_event(self, event: events.Event):
        handlers = self.event_handler_factory(type(event))

        for handler in handlers:
            uow = self.create_uow()
            try:
                logger.debug("handling event %r with handler %r", event, handler)
                handler.handle(event, uow)
                uow.commit()
            except Exception:  # pragma: no cover
                logger.exception("Exception handling event %r", event)
                uow.rollback()
                continue

            self._dispatch_pending_events(uow)

    def _handle_command(self, command: commands.Command):
        logger.debug("handling command %r", command)
        self._set_missing_command_fields(command)

        uow = self.create_uow()
        try:
            command_type = type(command)
            validated_command = command_type.model_validate(
                command.model_dump(round_trip=True), strict=True
            )
            handler = self.command_handler_factory(command_type)
            result = handler.handle(validated_command, uow)
            uow.commit()
        except Exception:
            logger.exception("Exception handling command %r", command)
            uow.rollback()
            raise

        self._dispatch_pending_events(uow)

        return result

    def _dispatch_pending_events(self, uow: AbstractUnitOfWork):
        for event in uow.collect_pending_events():
            self._dispatch_event(event)

    def _set_missing_command_fields(self, command):
        if not hasattr(command, "actor"):
            command.actor = self.app_context_provider.get_current_actor()
