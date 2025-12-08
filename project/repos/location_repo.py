from project.models import Location
from project.repos.base_repo import BaseRepo


class LocationRepo(BaseRepo[Location]):
    model_class = Location
