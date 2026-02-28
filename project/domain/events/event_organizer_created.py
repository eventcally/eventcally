from typing import Optional

from project.domain.events.image_created import ImageCreated
from project.domain.events.location_created import LocationCreated
from project.domain.types import ObjectId

from .base import Event


class EventOrganizerCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationCreated] = None
    logo: Optional[ImageCreated] = None
