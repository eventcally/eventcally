from __future__ import annotations

import logging

from project.application import queries
from project.application.abstract_query_handler_factory import (
    AbstractQueryHandlerFactory,
)
from project.application.abstract_read_session_scope import AbstractReadSessionScope
from project.application.services.abstract_app_context_provider import (
    AbstractAppContextProvider,
)

logger = logging.getLogger(__name__)


class QueryBus:
    """Dispatches queries to their handlers inside a read-session scope.

    No unit of work, commit or event dispatch: queries never mutate. Handlers must
    return fully materialized read models, because the read session is released
    when the scope exits.
    """

    def __init__(
        self,
        app_context_provider: AbstractAppContextProvider,
        query_handler_factory: AbstractQueryHandlerFactory,
        read_session_scope: AbstractReadSessionScope,
    ):
        self.app_context_provider = app_context_provider
        self.query_handler_factory = query_handler_factory
        self.read_session_scope = read_session_scope

    def handle(
        self, query: queries.Query[queries.QueryResultType]
    ) -> queries.QueryResultType:
        logger.debug("handling query %r", query)
        self._set_missing_query_fields(query)

        try:
            query_type = type(query)
            validated_query = query_type.model_validate(
                query.model_dump(round_trip=True), strict=True
            )
            handler = self.query_handler_factory(query_type)

            with self.read_session_scope:
                return handler.handle(validated_query)
        except Exception:
            logger.exception("Exception handling query %r", query)
            raise

    def _set_missing_query_fields(self, query: queries.Query):
        if query.actor is None:
            query.actor = self.app_context_provider.get_current_actor()
