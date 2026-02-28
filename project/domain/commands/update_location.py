from pydantic import BaseModel

from project.domain.types import Unsetable, unset


class UpdateLocation(BaseModel):
    street: Unsetable[str] = unset
    postalCode: Unsetable[str] = unset
    city: Unsetable[str] = unset
    state: Unsetable[str] = unset
    country: Unsetable[str] = unset
    latitude: Unsetable[float] = unset
    longitude: Unsetable[float] = unset
