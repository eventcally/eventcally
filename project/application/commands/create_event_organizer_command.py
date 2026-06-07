from typing import Optional

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateEventOrganizerCommandResult(CommandResult):
    id: ObjectId


class CreateEventOrganizerCommand(CommandWithResult[CreateEventOrganizerCommandResult]):
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationValueObject] = None
    logo: Optional[ImageValueObject] = None
