import abc
from typing import List, Optional

from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import (
    EventDateDetailReadModel,
    EventDateListItemReadModel,
    EventDateReadModel,
    EventDetailReadModel,
    EventEditReadModel,
)
from project.application.read_models.event_visibility_read_model import (
    EventVisibilityReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventDetailReadRepository(abc.ABC):
    @abc.abstractmethod
    def get_visibility(
        self, event_id: ObjectId
    ) -> Optional[EventVisibilityReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_visibility_of_date(
        self, event_date_id: ObjectId
    ) -> Optional[EventVisibilityReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_detail(
        self, event_id: ObjectId, reference_admin_unit_id: Optional[ObjectId]
    ) -> Optional[EventDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_for_edit(
        self, event_id: ObjectId
    ) -> Optional[EventEditReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_date_detail(
        self, event_date_id: ObjectId
    ) -> Optional[EventDateDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_dates_of_event(
        self, event_id: ObjectId, page_request: PageRequest
    ) -> Page[EventDateListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_upcoming_dates(
        self, event_id: ObjectId
    ) -> List[EventDateReadModel]:  # pragma: no cover
        raise NotImplementedError
