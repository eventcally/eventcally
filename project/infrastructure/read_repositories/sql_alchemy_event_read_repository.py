from typing import Optional

from project.application.read_models.event_read_model import EventReadModel
from project.application.read_repositories.abstract_event_read_repository import (
    AbstractEventReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.models.event import Event
from project.models.event_organizer import EventOrganizer
from project.models.event_place import EventPlace


class SqlAlchemyEventReadRepository(AbstractEventReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self, object_id: int) -> Optional[Event]:
        return self.session.query(Event).filter_by(id=object_id).first()

    def get(self, object_id: int) -> Optional[EventReadModel]:
        model = self._get_model(object_id)
        return Event.to_read_model(model)

    def _get_names(self, model_class, object_ids: set[ObjectId]) -> dict[ObjectId, str]:
        if not object_ids:
            return {}

        rows = (
            self.session.query(model_class.id, model_class.name)
            .filter(model_class.id.in_(object_ids))
            .all()
        )
        return dict(rows)

    def get_organizer_names(self, object_ids: set[ObjectId]) -> dict[ObjectId, str]:
        return self._get_names(EventOrganizer, object_ids)

    def get_place_names(self, object_ids: set[ObjectId]) -> dict[ObjectId, str]:
        return self._get_names(EventPlace, object_ids)
