"""Image created nested payload model."""

from typing import Optional

from project.domain.events.image_created import ImageCreated as ImageCreatedEvent
from project.domain.types.custom_base_model import CustomBaseModel
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class ImageCreated(CustomBaseModel):
    url: str
    encoding_format: Optional[str] = None
    copyright_text: Optional[str] = None
    license_id: Optional[int] = None

    @classmethod
    def from_event(cls, img: ImageCreatedEvent, ctx: WebhookMapperContext):
        if img is None:
            return None
        return cls(
            url=ctx.get_image_url(img.id, img.hash),
            encoding_format=img.encoding_format,
            copyright_text=img.copyright_text,
            license_id=img.license_id,
        )
