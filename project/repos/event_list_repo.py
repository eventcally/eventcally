from project.models import EventList
from project.repos.base_repo import BaseRepo


class EventListRepo(BaseRepo[EventList]):
    model_class = EventList
