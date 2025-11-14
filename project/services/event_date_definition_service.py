from project.models import EventDateDefinition
from project.services.base_service import BaseService


class EventDateDefinitionService(BaseService[EventDateDefinition]):
    model_class = EventDateDefinition
