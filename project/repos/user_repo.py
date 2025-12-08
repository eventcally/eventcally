from project.models import User
from project.repos.base_repo import BaseRepo


class UserRepo(BaseRepo[User]):
    model_class = User
