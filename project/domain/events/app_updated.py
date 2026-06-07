from typing import Optional

from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types import ChangedValue, ObjectId
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class AppUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    app_permissions: Optional[ChangedValue[list[str]]] = OptionalChangedValueField()
    redirect_uris: Optional[ChangedValue[list[str]]] = OptionalChangedValueField()
    scope: Optional[ChangedValue[str]] = OptionalChangedValueField()
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    homepage_url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    setup_url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    webhook: Optional[ChangedValue[WebhookValueObject]] = OptionalChangedValueField()
