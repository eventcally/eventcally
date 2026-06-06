from typing import Optional

from project.application.read_models.event_read_model import EventReadModel
from project.application.read_repositories.abstract_event_read_repository import (
    AbstractEventReadRepository,
)
from project.models.event import Event


class SqlAlchemyEventReadRepository(AbstractEventReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self, object_id: int) -> Optional[Event]:
        return self.session.query(Event).filter_by(id=object_id).first()

    def get(self, object_id: int) -> Optional[EventReadModel]:
        model = self._get_model(object_id)
        return Event.to_read_model(model)
