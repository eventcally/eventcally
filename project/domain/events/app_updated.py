from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types import (
    ObjectId,
    OptionalChangedOptionalValue,
    OptionalChangedValue,
)
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class AppUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: OptionalChangedValue[str] = OptionalChangedValueField()
    app_permissions: OptionalChangedValue[set[str]] = OptionalChangedValueField()
    redirect_uris: OptionalChangedValue[set[str]] = OptionalChangedValueField()
    scope: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    description: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    homepage_url: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    setup_url: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    webhook: OptionalChangedOptionalValue[WebhookValueObject] = (
        OptionalChangedValueField()
    )
