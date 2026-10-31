import abc
from typing import List, Optional

from project.application.queries.list_custom_event_categories_query import (
    ListCustomEventCategoriesQuery,
)
from project.application.queries.list_custom_event_category_sets_query import (
    ListCustomEventCategorySetsQuery,
)
from project.application.queries.list_event_categories_query import (
    ListEventCategoriesQuery,
)
from project.application.queries.list_licenses_query import ListLicensesQuery
from project.application.queries.lookup_custom_event_categories_query import (
    LookupCustomEventCategoriesQuery,
)
from project.application.read_models.image_read_model import LicenseRefReadModel
from project.application.read_models.page import Page
from project.application.read_models.reference_data_read_models import (
    CustomEventCategoryRefReadModel,
    CustomEventCategorySetRefReadModel,
    EventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractReferenceDataReadRepository(abc.ABC):
    """Platform-wide lookup data: licenses and (custom) event categories."""

    @abc.abstractmethod
    def list_licenses(
        self, query: ListLicensesQuery
    ) -> Page[LicenseRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_event_categories(
        self, query: ListEventCategoriesQuery
    ) -> Page[EventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_custom_event_category_sets(
        self, query: ListCustomEventCategorySetsQuery
    ) -> Page[CustomEventCategorySetRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_custom_event_categories(
        self, query: ListCustomEventCategoriesQuery
    ) -> Page[CustomEventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_all_event_categories(
        self,
    ) -> List[EventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_event_category(
        self, category_id: ObjectId
    ) -> Optional[EventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_event_category_by_name(
        self, name: str
    ) -> Optional[EventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def lookup_custom_event_categories(
        self, query: LookupCustomEventCategoriesQuery
    ) -> Page[CustomEventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_custom_event_category(
        self, category_id: ObjectId
    ) -> Optional[CustomEventCategoryRefReadModel]:  # pragma: no cover
        raise NotImplementedError
