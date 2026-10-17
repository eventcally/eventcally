import abc
from typing import Optional

from project.application.queries.list_custom_widgets_query import ListCustomWidgetsQuery
from project.application.read_models.custom_widget_read_models import (
    CustomWidgetReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractCustomWidgetReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListCustomWidgetsQuery
    ) -> Page[CustomWidgetReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[CustomWidgetReadModel]:  # pragma: no cover
        raise NotImplementedError
