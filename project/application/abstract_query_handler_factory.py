import abc

from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)


class AbstractQueryHandlerFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(
        self, query_type: type[queries.Query]
    ) -> AbstractQueryHandler:  # pragma: no cover
        raise NotImplementedError
