import abc
from typing import List, Optional

from project.application.queries.list_event_place_suggestions_query import (
    ListEventPlaceSuggestionsQuery,
)
from project.application.queries.list_event_places_query import ListEventPlacesQuery
from project.application.queries.lookup_event_places_query import LookupEventPlacesQuery
from project.application.read_models.event_place_read_models import (
    EventPlaceDetailReadModel,
    EventPlaceEditReadModel,
    EventPlaceListItemReadModel,
    EventPlaceSuggestionReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventPlaceReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListEventPlacesQuery
    ) -> Page[EventPlaceListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[EventPlaceDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_for_edit(
        self, object_id: ObjectId
    ) -> Optional[EventPlaceEditReadModel]:  # pragma: no cover
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
    def list_suggestions(
        self, query: ListEventPlaceSuggestionsQuery
    ) -> List[EventPlaceSuggestionReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def lookup(
        self, query: LookupEventPlacesQuery
    ) -> Page[EventPlaceSuggestionReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_ref(
        self, admin_unit_id: ObjectId, object_id: ObjectId
    ) -> Optional[EventPlaceSuggestionReadModel]:  # pragma: no cover
        raise NotImplementedError
