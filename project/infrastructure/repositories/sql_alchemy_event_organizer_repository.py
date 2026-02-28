from project.domain.repositories import AbstractEventOrganizerRepository
from project.models.event_organizer import EventOrganizer


class SqlAlchemyEventOrganizerRepository(AbstractEventOrganizerRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event_organizer: EventOrganizer):
        self.session.add(event_organizer)

    def _get(self, object_id: int) -> EventOrganizer:
        return self.session.query(EventOrganizer).filter_by(id=object_id).first()

    def _remove(self, event_organizer: EventOrganizer):
        self.session.delete(event_organizer)
