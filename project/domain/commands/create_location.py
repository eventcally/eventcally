from typing import Optional

from pydantic import BaseModel


class CreateLocation(BaseModel):
    street: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
