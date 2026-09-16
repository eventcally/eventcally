from project.models import EventReference
from project.repos.base_repo import BaseRepo


class EventReferenceRepo(BaseRepo[EventReference]):
    model_class = EventReference
