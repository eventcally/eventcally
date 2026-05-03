from typing import Optional

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import ChangedValue
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class LocationUpdated(CustomBaseModel, HasChangedValueMixin):
    street: Optional[ChangedValue[str]] = OptionalChangedValueField()
    postalCode: Optional[ChangedValue[str]] = OptionalChangedValueField()
    city: Optional[ChangedValue[str]] = OptionalChangedValueField()
    state: Optional[ChangedValue[str]] = OptionalChangedValueField()
    country: Optional[ChangedValue[str]] = OptionalChangedValueField()
    latitude: Optional[ChangedValue[float]] = OptionalChangedValueField()
    longitude: Optional[ChangedValue[float]] = OptionalChangedValueField()

    def has_changed_values(self) -> bool:
        return self._has_set_changed_values()
