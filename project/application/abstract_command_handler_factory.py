import abc

from project.application import commands
from project.application.command_handlers.abstract_command_handler import (
    AbstractCommandHandler,
)


class AbstractCommandHandlerFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, command_type: type[commands.Command]
    ) -> AbstractCommandHandler:  # pragma: no cover
        raise NotImplementedError
