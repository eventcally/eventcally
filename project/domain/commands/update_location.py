from project.domain.types import Unsetable
from project.domain.types.custom_base_model import CustomBaseModel
from project.domain.types.unset_field_factory import UnsetField


class UpdateLocation(CustomBaseModel):
    street: Unsetable[str] = UnsetField()
    postalCode: Unsetable[str] = UnsetField()
    city: Unsetable[str] = UnsetField()
    state: Unsetable[str] = UnsetField()
    country: Unsetable[str] = UnsetField()
    latitude: Unsetable[float] = UnsetField()
    longitude: Unsetable[float] = UnsetField()
