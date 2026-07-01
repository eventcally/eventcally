from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class WebhookValueObject(CustomBaseModel):
    url: str
    secret: Optional[str] = None
    disabled: bool = False
    event_types: set[str] = set()

    def is_enabled_for_event_type(self, event_type: str) -> bool:
        return (
            self.url
            and not self.disabled
            and (self.event_types and event_type in self.event_types)
        )
