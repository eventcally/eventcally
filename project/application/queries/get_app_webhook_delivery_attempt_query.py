from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryAttemptReadModel,
)
from project.domain.types.object_id import ObjectId


class GetAppWebhookDeliveryAttemptQuery(
    Query[Optional[AppWebhookDeliveryAttemptReadModel]]
):
    """`None` if the attempt does not exist. Requires
    `webhook_delivery_attempts:read` on its app's organization."""

    id: ObjectId
