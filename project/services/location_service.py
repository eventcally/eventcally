from project.models import Location
from project.services.base_service import BaseService


class LocationService(BaseService[Location]):
    model_class = Location
