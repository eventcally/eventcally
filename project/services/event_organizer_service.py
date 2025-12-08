from project.models import EventOrganizer
from project.services.base_service import BaseService


class EventOrganizerService(BaseService[EventOrganizer]):
    model_class = EventOrganizer
