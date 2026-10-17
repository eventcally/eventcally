from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryAttemptReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListWebhookDeliveryAttemptsForAppQuery(
    Query[Optional[Page[AppWebhookDeliveryAttemptReadModel]]]
):
    """Attempts of a delivery of `app_id` (the authenticated app), newest first;
    `None` unless the delivery belongs to the app."""

    app_id: ObjectId
    webhook_delivery_id: ObjectId
    page: PageRequest = PageRequest()
