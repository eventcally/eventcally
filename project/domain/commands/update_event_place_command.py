from project.domain.types import ObjectId, Unsetable
from project.domain.types.unset_field_factory import UnsetField

from .base import Command
from .update_image import UpdateImage
from .update_location import UpdateLocation


class UpdateEventPlaceCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    url: Unsetable[str] = UnsetField()
    description: Unsetable[str] = UnsetField()
    location: Unsetable[UpdateLocation] = UnsetField()
    photo: Unsetable[UpdateImage] = UnsetField()
