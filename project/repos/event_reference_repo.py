from project.models import EventReference
from project.repos.base_repo import BaseRepo


class EventReferenceRepo(BaseRepo[EventReference]):
    model_class = EventReference

    def create_event_reference(
        self, event_id: int, admin_unit_id: int, rating: int = 50
    ) -> EventReference:
        event_reference = EventReference(
            event_id=event_id, admin_unit_id=admin_unit_id, rating=rating
        )
        self.insert_object(event_reference)
        return event_reference

    def get_event_reference_by_event_id(
        self, event_id: int, admin_unit_id: int
    ) -> EventReference:
        return (
            self.db.session.query(EventReference)
            .filter(EventReference.event_id == event_id)
            .filter(EventReference.admin_unit_id == admin_unit_id)
            .first()
        )
