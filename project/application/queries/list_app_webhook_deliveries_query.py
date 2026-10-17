from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppWebhookDeliveriesQuery(Query[Optional[Page[AppWebhookDeliveryReadModel]]]):
    """Webhook deliveries of an app, newest first; `None` if the app does not
    exist. Requires `webhook_deliveries:read` on the app's organization."""

    app_id: ObjectId
    page: PageRequest = PageRequest()
