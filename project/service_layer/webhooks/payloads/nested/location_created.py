"""Location created nested payload model."""

from typing import Optional

from project.domain.events.location_created import (
    LocationCreated as LocationCreatedEvent,
)
from project.domain.types.custom_base_model import CustomBaseModel
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class LocationCreated(CustomBaseModel):
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @classmethod
    def from_event(cls, loc: LocationCreatedEvent, ctx: WebhookMapperContext):
        if loc is None:
            return None
        return cls(
            street=loc.street,
            postal_code=loc.postalCode,
            city=loc.city,
            state=loc.state,
            country=loc.country,
            latitude=loc.latitude,
            longitude=loc.longitude,
        )
