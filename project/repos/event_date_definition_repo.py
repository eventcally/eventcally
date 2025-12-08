from project.models import EventDateDefinition
from project.repos.base_repo import BaseRepo


class EventDateDefinitionRepo(BaseRepo[EventDateDefinition]):
    model_class = EventDateDefinition
