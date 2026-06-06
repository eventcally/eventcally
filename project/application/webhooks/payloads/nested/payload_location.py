"""Location created nested payload model."""

from typing import Optional

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types.custom_base_model import CustomBaseModel


class PayloadLocation(CustomBaseModel):
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @classmethod
    def from_event(cls, loc: LocationValueObject, ctx: AbstractWebhookMapperContext):
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
