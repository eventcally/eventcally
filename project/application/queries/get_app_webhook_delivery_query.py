from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryReadModel,
)
from project.domain.types.object_id import ObjectId


class GetAppWebhookDeliveryQuery(Query[Optional[AppWebhookDeliveryReadModel]]):
    """`None` if the delivery does not exist. Requires `webhook_deliveries:read`
    on its app's organization."""

    id: ObjectId
