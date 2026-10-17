from project.application import queries
from project.application.abstract_query_handler_factory import (
    AbstractQueryHandlerFactory,
)
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)


class QueryHandlerFactory(AbstractQueryHandlerFactory):
    def __init__(self, factory_aggregate):
        self.factory_aggregate = factory_aggregate

    def __call__(self, query_type: type[queries.Query]) -> AbstractQueryHandler:
        return self.factory_aggregate(query_type)
