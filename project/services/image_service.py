from project.models import Image
from project.services.base_service import BaseService


class ImageService(BaseService[Image]):
    model_class = Image
