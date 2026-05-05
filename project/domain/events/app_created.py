from typing import Optional

from project.domain.events.webhook_created import WebhookCreated
from project.domain.types import ObjectId

from .base import Event


class AppCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    webhook: Optional[WebhookCreated] = None
