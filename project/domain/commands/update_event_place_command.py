from project.domain.types import ObjectId, Unsetable, unset

from .base import Command
from .update_image import UpdateImage
from .update_location import UpdateLocation


class UpdateEventPlaceCommand(Command):
    id: ObjectId
    name: Unsetable[str] = unset
    url: Unsetable[str] = unset
    description: Unsetable[str] = unset
    location: Unsetable[UpdateLocation] = unset
    photo: Unsetable[UpdateImage] = unset
