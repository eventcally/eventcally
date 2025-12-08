from project.models import EventPlace
from project.services.base_service import BaseService


class EventPlaceService(BaseService[EventPlace]):
    model_class = EventPlace
