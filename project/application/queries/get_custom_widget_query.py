from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.custom_widget_read_models import (
    CustomWidgetReadModel,
)
from project.domain.types.object_id import ObjectId


class GetCustomWidgetQuery(Query[Optional[CustomWidgetReadModel]]):
    """`None` if the widget does not exist. Public: embedded widgets load their
    configuration without authentication."""

    id: ObjectId
