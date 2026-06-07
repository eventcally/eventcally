"""Image created nested payload model."""

from typing import Optional

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.types.custom_base_model import CustomBaseModel


class PayloadImage(CustomBaseModel):
    url: str
    encoding_format: str
    copyright_text: Optional[str] = None
    license_id: Optional[int] = None

    @classmethod
    def from_event(
        cls, img: Optional[ImageForEvent], ctx: AbstractWebhookMapperContext
    ):
        if img is None:
            return None
        return cls(
            url=ctx.get_image_url(img.id, img.hash),
            encoding_format=img.encoding_format,
            copyright_text=img.copyright_text,
            license_id=img.license_id,
        )
