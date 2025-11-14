from project.models import EventDate
from project.services.base_service import BaseService


class EventDateService(BaseService[EventDate]):
    model_class = EventDate
