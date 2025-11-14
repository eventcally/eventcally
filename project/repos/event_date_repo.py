from project.models import EventDate
from project.repos.base_repo import BaseRepo


class EventDateRepo(BaseRepo[EventDate]):
    model_class = EventDate
