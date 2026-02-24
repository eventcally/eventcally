from typing import Optional

from project.domain.events.image_created import ImageCreated
from project.domain.events.location_created import LocationCreated
from project.domain.types import ObjectId

from .base import Event


class EventPlaceCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationCreated] = None
    photo: Optional[ImageCreated] = None
