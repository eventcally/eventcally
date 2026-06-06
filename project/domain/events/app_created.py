from typing import Optional

from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types import ObjectId

from .base import Event


class AppCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    app_permissions: list[str]
    redirect_uris: Optional[list[str]] = None
    scope: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    webhook: Optional[WebhookValueObject] = None
