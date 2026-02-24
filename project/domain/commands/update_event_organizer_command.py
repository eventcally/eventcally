from project.domain.types import ObjectId, Unsetable, unset

from .base import Command
from .update_image import UpdateImage
from .update_location import UpdateLocation


class UpdateEventOrganizerCommand(Command):
    id: ObjectId
    name: Unsetable[str] = unset
    url: Unsetable[str] = unset
    email: Unsetable[str] = unset
    phone: Unsetable[str] = unset
    fax: Unsetable[str] = unset
    location: Unsetable[UpdateLocation] = unset
    logo: Unsetable[UpdateImage] = unset
