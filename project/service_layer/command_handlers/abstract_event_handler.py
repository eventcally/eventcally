from abc import ABC, abstractmethod
from typing import Any

from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork


class AbstractEventHandler(ABC):
    @abstractmethod
    def handle(
        self, event: events.Event, uow: AbstractUnitOfWork
    ) -> Any:  # pragma: no cover
        raise NotImplementedError
