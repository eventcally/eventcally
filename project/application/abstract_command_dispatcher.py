import abc

from project.application import commands


class AbstractCommandDispatcher(abc.ABC):
    @abc.abstractmethod
    def dispatch(self, command: commands.Command):  # pragma: no cover
        raise NotImplementedError
