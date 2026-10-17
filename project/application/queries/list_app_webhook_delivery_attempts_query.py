from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryAttemptReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppWebhookDeliveryAttemptsQuery(
    Query[Optional[Page[AppWebhookDeliveryAttemptReadModel]]]
):
    """Attempts of a webhook delivery in id order; `None` if the delivery does not
    exist. Requires `webhook_delivery_attempts:read` on its app's organization."""

    webhook_delivery_id: ObjectId
    page: PageRequest = PageRequest()
