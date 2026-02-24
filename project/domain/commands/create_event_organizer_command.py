from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult
from .create_image import CreateImage
from .create_location import CreateLocation


class CreateEventOrganizerCommandResult(CommandResult):
    id: ObjectId


class CreateEventOrganizerCommand(CommandWithResult[CreateEventOrganizerCommandResult]):
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[CreateLocation] = None
    logo: Optional[CreateImage] = None
