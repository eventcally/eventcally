from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_child_read_models import (
    AppWebhookDeliveryReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListWebhookDeliveriesForAppQuery(Query[Page[AppWebhookDeliveryReadModel]]):
    """Webhook deliveries of `app_id` (the authenticated app), newest event first."""

    app_id: ObjectId
    page: PageRequest = PageRequest()
