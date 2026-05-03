from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class WebhookCreated(CustomBaseModel):
    url: str
    secret: Optional[str] = None
    disabled: bool = False
    event_types: list[str] = []
