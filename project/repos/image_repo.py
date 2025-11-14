from project.models import Image
from project.repos.base_repo import BaseRepo


class ImageRepo(BaseRepo[Image]):
    model_class = Image
