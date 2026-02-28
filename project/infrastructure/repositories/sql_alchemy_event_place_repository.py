from project.domain.repositories import AbstractEventPlaceRepository
from project.models.event_place import EventPlace


class SqlAlchemyEventPlaceRepository(AbstractEventPlaceRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event_place: EventPlace):
        self.session.add(event_place)

    def _get(self, object_id: int) -> EventPlace:
        return self.session.query(EventPlace).filter_by(id=object_id).first()

    def _remove(self, event_place: EventPlace):
        self.session.delete(event_place)
