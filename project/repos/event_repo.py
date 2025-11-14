from project.models import Event
from project.repos.base_repo import BaseRepo


class EventRepo(BaseRepo[Event]):
    model_class = Event
