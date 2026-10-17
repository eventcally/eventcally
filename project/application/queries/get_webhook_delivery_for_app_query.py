from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryReadModel,
)
from project.domain.types.object_id import ObjectId


class GetWebhookDeliveryForAppQuery(Query[Optional[AppWebhookDeliveryReadModel]]):
    """`None` unless the delivery belongs to `app_id` (the authenticated app)."""

    app_id: ObjectId
    id: ObjectId
