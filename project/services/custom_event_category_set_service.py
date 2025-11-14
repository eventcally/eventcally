from project.models import CustomEventCategorySet
from project.services.base_service import BaseService


class CustomEventCategorySetService(BaseService[CustomEventCategorySet]):
    model_class = CustomEventCategorySet
