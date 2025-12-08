from project.models import CustomEventCategory
from project.repos.base_repo import BaseRepo


class CustomEventCategoryRepo(BaseRepo[CustomEventCategory]):
    model_class = CustomEventCategory
