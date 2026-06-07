from pydantic import field_validator

from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateAppCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    app_permissions: Unsetable[list[str]] = UnsetField()
    redirect_uris: NullableUnsetable[list[str]] = UnsetField()
    scope: NullableUnsetable[str] = UnsetField()
    description: NullableUnsetable[str] = UnsetField()
    homepage_url: NullableUnsetable[str] = UnsetField()
    setup_url: NullableUnsetable[str] = UnsetField()
    webhook: NullableUnsetable[WebhookValueObject] = UnsetField()

    @field_validator("app_permissions")
    @classmethod
    def validate_app_permissions_not_empty(cls, v):
        if v is not None and len(v) < 1:
            raise ValueError("app_permissions must contain at least one permission")
        return v
