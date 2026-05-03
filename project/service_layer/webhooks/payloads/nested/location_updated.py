"""Location updated nested payload model."""

from typing import Optional

from project.domain.events.location_updated import (
    LocationUpdated as LocationUpdatedEvent,
)
from project.domain.types import ChangedValue, unset
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unsetable import Unsetable
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class LocationUpdated(CustomBaseModel):
    street: Optional[ChangedValue[str]] = OptionalChangedValueField()
    postal_code: Optional[ChangedValue[str]] = OptionalChangedValueField()
    city: Optional[ChangedValue[str]] = OptionalChangedValueField()
    state: Optional[ChangedValue[str]] = OptionalChangedValueField()
    country: Optional[ChangedValue[str]] = OptionalChangedValueField()
    latitude: Optional[ChangedValue[float]] = OptionalChangedValueField()
    longitude: Optional[ChangedValue[float]] = OptionalChangedValueField()

    @classmethod
    def from_event(
        cls, loc: Unsetable[LocationUpdatedEvent], ctx: WebhookMapperContext
    ):
        if loc == unset:
            return unset
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
