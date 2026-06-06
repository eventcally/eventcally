from project.application import commands
from project.application.abstract_command_handler_factory import (
    AbstractCommandHandlerFactory,
)
from project.application.command_handlers.abstract_command_handler import (
    AbstractCommandHandler,
)


class CommandHandlerFactory(AbstractCommandHandlerFactory):
    def __init__(self, factory_aggregate):
        self.factory_aggregate = factory_aggregate

    def __call__(self, command_type: type[commands.Command]) -> AbstractCommandHandler:
        return self.factory_aggregate(command_type)
