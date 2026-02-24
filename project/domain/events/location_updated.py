from typing import Optional

from pydantic import BaseModel

from project.domain.types import ChangedValue


class LocationUpdated(BaseModel):
    street: Optional[ChangedValue[str]] = None
    postalCode: Optional[ChangedValue[str]] = None
    city: Optional[ChangedValue[str]] = None
    state: Optional[ChangedValue[str]] = None
    country: Optional[ChangedValue[str]] = None
    latitude: Optional[ChangedValue[float]] = None
    longitude: Optional[ChangedValue[float]] = None

    def has_changed_values(self) -> bool:
        return len(self.model_fields_set) > 0
