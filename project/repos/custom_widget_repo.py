from project.models import CustomWidget
from project.repos.base_repo import BaseRepo


class CustomWidgetRepo(BaseRepo[CustomWidget]):
    model_class = CustomWidget
