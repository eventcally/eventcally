from typing import Optional

from pydantic import BaseModel

from project.domain.events.has_changed_value_mixin import HasChangedValueMixin
from project.domain.types import ChangedValue


class LocationUpdated(BaseModel, HasChangedValueMixin):
    street: Optional[ChangedValue[str]] = None
    postalCode: Optional[ChangedValue[str]] = None
    city: Optional[ChangedValue[str]] = None
    state: Optional[ChangedValue[str]] = None
    country: Optional[ChangedValue[str]] = None
    latitude: Optional[ChangedValue[float]] = None
    longitude: Optional[ChangedValue[float]] = None

    def has_changed_values(self) -> bool:
        return self._has_set_changed_values()
