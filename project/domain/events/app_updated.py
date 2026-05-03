from typing import Optional

from project.domain.events.webhook_updated import WebhookUpdated
from project.domain.types import ChangedValue, ObjectId, Unsetable
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unset_field_factory import UnsetField

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
    webhook: Unsetable[WebhookUpdated] = UnsetField()
