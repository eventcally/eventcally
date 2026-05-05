"""Image updated nested payload model."""

from typing import Optional

from project.domain.events.image_updated import ImageUpdated as ImageUpdatedEvent
from project.domain.types import ChangedValue, unset
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unsetable import Unsetable
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class ImageUpdated(CustomBaseModel):
    url: str
    data_changed: bool = False
    encoding_format: Optional[ChangedValue[str]] = OptionalChangedValueField()
    copyright_text: Optional[ChangedValue[Optional[str]]] = OptionalChangedValueField()
    license_id: Optional[ChangedValue[Optional[int]]] = OptionalChangedValueField()

    @classmethod
    def from_event(cls, img: Unsetable[ImageUpdatedEvent], ctx: WebhookMapperContext):
        if img == unset:
            return unset
        if img is None:
            return None
        return cls(
            url=ctx.get_image_url(img.id, img.hash),
            data_changed=img.data_changed,
            encoding_format=img.encoding_format,
            copyright_text=img.copyright_text,
            license_id=img.license_id,
        )
