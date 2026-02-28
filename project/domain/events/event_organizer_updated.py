from typing import Optional

from project.domain.events.image_updated import ImageUpdated
from project.domain.events.location_updated import LocationUpdated
from project.domain.types import ChangedValue, ObjectId, Unsetable, unset

from .base import Event


class EventOrganizerUpdated(Event):
    id: ObjectId
    name: Optional[ChangedValue[str]] = None
    url: Optional[ChangedValue[str]] = None
    email: Optional[ChangedValue[str]] = None
    phone: Optional[ChangedValue[str]] = None
    fax: Optional[ChangedValue[str]] = None
    location: Unsetable[LocationUpdated] = unset
    logo: Unsetable[ImageUpdated] = unset
