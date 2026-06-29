from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class LocationValueObject(CustomBaseModel):
    street: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def is_empty(self) -> bool:
        return (
            not self.street
            and not self.postalCode
            and not self.city
            and not self.state
            and not self.country
            and not self.latitude
            and not self.longitude
        )

    @classmethod
    def compare(
        cls, old: "Optional[LocationValueObject]", new: "Optional[LocationValueObject]"
    ) -> bool:
        is_old_empty = old is None or old.is_empty()
        is_new_empty = new is None or new.is_empty()
        if is_old_empty or is_new_empty:
            return is_old_empty and is_new_empty

        return old == new
