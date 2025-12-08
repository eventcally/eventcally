from project.models import EventPlace
from project.repos.base_repo import BaseRepo


class EventPlaceRepo(BaseRepo[EventPlace]):
    model_class = EventPlace
