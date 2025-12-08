from project.models import UserFavoriteEvents
from project.services.base_service import BaseService


class UserFavoriteEventsService(BaseService[UserFavoriteEvents]):
    model_class = UserFavoriteEvents
