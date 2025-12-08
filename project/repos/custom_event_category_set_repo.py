from project.models import CustomEventCategorySet
from project.repos.base_repo import BaseRepo


class CustomEventCategorySetRepo(BaseRepo[CustomEventCategorySet]):
    model_class = CustomEventCategorySet
