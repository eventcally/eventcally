from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult
from .create_image import CreateImage
from .create_location import CreateLocation


class CreateEventPlaceCommandResult(CommandResult):
    id: ObjectId


class CreateEventPlaceCommand(CommandWithResult[CreateEventPlaceCommandResult]):
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[CreateLocation] = None
    photo: Optional[CreateImage] = None
