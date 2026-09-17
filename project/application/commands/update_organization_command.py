from typing import List

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateOrganizationCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    short_name: Unsetable[str] = UnsetField()
    description: NullableUnsetable[str] = UnsetField()
    url: NullableUnsetable[str] = UnsetField()
    email: NullableUnsetable[str] = UnsetField()
    phone: NullableUnsetable[str] = UnsetField()
    fax: NullableUnsetable[str] = UnsetField()
    location: NullableUnsetable[LocationValueObject] = UnsetField()
    logo: NullableUnsetable[ImageValueObject] = UnsetField()
    incoming_verification_requests_allowed: Unsetable[bool] = UnsetField()
    incoming_verification_requests_text: NullableUnsetable[str] = UnsetField()
    incoming_verification_requests_postal_codes: Unsetable[List[str]] = UnsetField()
