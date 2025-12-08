from project.models import EventList
from project.services.base_service import BaseService


class EventListService(BaseService[EventList]):
    model_class = EventList
