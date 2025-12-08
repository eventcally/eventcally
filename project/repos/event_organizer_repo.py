from project.models import EventOrganizer
from project.repos.base_repo import BaseRepo


class EventOrganizerRepo(BaseRepo[EventOrganizer]):
    model_class = EventOrganizer
