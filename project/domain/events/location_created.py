from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class LocationCreated(CustomBaseModel):
    street: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
