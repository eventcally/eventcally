import abc
from typing import List

from project.application.queries.list_dump_event_references_query import (
    ListDumpEventReferencesQuery,
)
from project.application.queries.list_dump_events_query import ListDumpEventsQuery
from project.application.queries.list_dump_organizations_query import (
    ListDumpOrganizationsQuery,
)
from project.application.queries.list_dump_organizers_query import (
    ListDumpOrganizersQuery,
)
from project.application.queries.list_dump_places_query import ListDumpPlacesQuery
from project.application.read_models.batch_read_models import (
    DumpEventReferenceReadModel,
    DumpOrganizerReadModel,
    SitemapEventReadModel,
)
from project.application.read_models.event_read_models import (
    EventDetailReadModel,
    EventOrganizationReadModel,
    EventPlaceEmbedReadModel,
)
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractBatchReadRepository(abc.ABC):
    """Reads of the background jobs. Batches are keyset pages by id, so a job loops
    until a batch comes back empty without holding one big result."""

    @abc.abstractmethod
    def list_dump_events(
        self, query: ListDumpEventsQuery
    ) -> List[EventDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dump_places(
        self, query: ListDumpPlacesQuery
    ) -> List[EventPlaceEmbedReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dump_organizers(
        self, query: ListDumpOrganizersQuery
    ) -> List[DumpOrganizerReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dump_organizations(
        self, query: ListDumpOrganizationsQuery
    ) -> List[EventOrganizationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dump_event_categories(
        self,
    ) -> List[EventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dump_event_references(
        self, query: ListDumpEventReferencesQuery
    ) -> List[DumpEventReferenceReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_sitemap_events(
        self,
    ) -> List[SitemapEventReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_organization_ids_due_for_deletion(
        self,
    ) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_user_ids_due_for_deletion(self) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_ghost_user_ids(self) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_old_event_ids(self) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_recurring_event_ids(self) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError
