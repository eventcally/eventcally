from project.models import UserFavoriteEvents
from project.repos.base_repo import BaseRepo


class UserFavoriteEventsRepo(BaseRepo[UserFavoriteEvents]):
    model_class = UserFavoriteEvents
