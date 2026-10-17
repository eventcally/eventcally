from abc import ABC, abstractmethod
from typing import Any

from project.application import queries


class AbstractQueryHandler(ABC):
    """Answers one query type with fully materialized read models.

    Read repositories are constructor-injected; there is no unit of work.
    """

    @abstractmethod
    def handle(self, query: queries.Query) -> Any:  # pragma: no cover
        raise NotImplementedError
