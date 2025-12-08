from project.models import CustomWidget
from project.services.base_service import BaseService


class CustomWidgetService(BaseService[CustomWidget]):
    model_class = CustomWidget
