from project.models import CustomEventCategory
from project.services.base_service import BaseService


class CustomEventCategoryService(BaseService[CustomEventCategory]):
    model_class = CustomEventCategory
