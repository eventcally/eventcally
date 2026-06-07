from typing import Optional

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateEventPlaceCommandResult(CommandResult):
    id: ObjectId


class CreateEventPlaceCommand(CommandWithResult[CreateEventPlaceCommandResult]):
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationValueObject] = None
    photo: Optional[ImageValueObject] = None
