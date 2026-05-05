from pydantic import field_validator

from project.domain.commands.update_webhook import UpdateWebhook
from project.domain.types import ObjectId, Unsetable
from project.domain.types.unset_field_factory import UnsetField

from .base import Command


class UpdateAppCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    app_permissions: Unsetable[list[str]] = UnsetField()
    redirect_uris: Unsetable[list[str]] = UnsetField()
    scope: Unsetable[str] = UnsetField()
    description: Unsetable[str] = UnsetField()
    homepage_url: Unsetable[str] = UnsetField()
    setup_url: Unsetable[str] = UnsetField()
    webhook: Unsetable[UpdateWebhook] = UnsetField()

    @field_validator("app_permissions")
    @classmethod
    def validate_app_permissions_not_empty(cls, v):
        if v is not None and len(v) < 1:
            raise ValueError("app_permissions must contain at least one permission")
        return v
