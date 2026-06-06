from abc import ABC, abstractmethod
from typing import Any

from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork


class AbstractCommandHandler(ABC):
    @abstractmethod
    def handle(
        self, cmd: commands.Command, uow: AbstractUnitOfWork
    ) -> Any:  # pragma: no cover
        raise NotImplementedError
