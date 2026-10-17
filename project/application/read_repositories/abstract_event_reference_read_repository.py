import abc
from typing import Optional

from project.application.queries.list_incoming_event_references_query import (
    ListIncomingEventReferencesQuery,
)
from project.application.queries.list_outgoing_event_references_query import (
    ListOutgoingEventReferencesQuery,
)
from project.application.read_models.event_reference_read_models import (
    EventReferenceReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventReferenceReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_incoming(
        self, query: ListIncomingEventReferencesQuery
    ) -> Page[EventReferenceReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_outgoing(
        self, query: ListOutgoingEventReferencesQuery
    ) -> Page[EventReferenceReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[EventReferenceReadModel]:  # pragma: no cover
        raise NotImplementedError
