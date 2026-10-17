import abc
from typing import Optional

from project.application.queries.list_incoming_event_reference_requests_query import (
    ListIncomingEventReferenceRequestsQuery,
)
from project.application.queries.list_outgoing_event_reference_requests_query import (
    ListOutgoingEventReferenceRequestsQuery,
)
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventReferenceRequestReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_incoming(
        self, query: ListIncomingEventReferenceRequestsQuery
    ) -> Page[EventReferenceRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_outgoing(
        self, query: ListOutgoingEventReferenceRequestsQuery
    ) -> Page[EventReferenceRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[EventReferenceRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def auto_verifies(
        self, source_admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> bool:  # pragma: no cover
        """Whether `source` auto-verifies the reference requests of `target`."""
        raise NotImplementedError
