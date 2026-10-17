from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class LocationReadModel(BaseReadModel):
    """Attribute names match `LocationSchema` and `get_location_str` (`postalCode`).

    Coordinates stay `Decimal`, as loaded from the numeric columns, so `NumericStr`
    dumps them with the same digits.
    """

    model_config = ConfigDict(frozen=True)

    street: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    @property
    def coordinate(self) -> Optional[bool]:
        """Truthy where the ORM `Location.coordinate` geometry is set (for the
        structured data and iCal, which only test for presence)."""
        if self.latitude is not None and self.longitude is not None:
            return True

        return None
