from project.models import EventReferenceRequest
from project.repos.base_repo import BaseRepo


class EventReferenceRequestRepo(BaseRepo[EventReferenceRequest]):
    model_class = EventReferenceRequest
