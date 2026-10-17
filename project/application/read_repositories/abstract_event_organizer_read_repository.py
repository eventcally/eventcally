import abc
from typing import Optional

from project.application.queries.list_event_organizers_query import (
    ListEventOrganizersQuery,
)
from project.application.queries.lookup_event_organizers_query import (
    LookupEventOrganizersQuery,
)
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerDetailReadModel,
    EventOrganizerEditReadModel,
    EventOrganizerListItemReadModel,
    EventOrganizerRefReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventOrganizerReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListEventOrganizersQuery
    ) -> Page[EventOrganizerListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[EventOrganizerDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_for_edit(
        self, object_id: ObjectId
    ) -> Optional[EventOrganizerEditReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def lookup(
        self, query: LookupEventOrganizersQuery
    ) -> Page[EventOrganizerRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_ref(
        self, admin_unit_id: ObjectId, object_id: ObjectId
    ) -> Optional[EventOrganizerRefReadModel]:  # pragma: no cover
        raise NotImplementedError
