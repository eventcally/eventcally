from project.models import EventReference
from project.models.event_reference_request import EventReferenceRequest
from project.repos.event_reference_repo import EventReferenceRepo
from project.services.base_service import BaseService


class EventReferenceService(BaseService[EventReference]):
    def __init__(self, repo: EventReferenceRepo, context_provider, **kwargs):
        super().__init__(repo, context_provider, **kwargs)
        self.repo: EventReferenceRepo = repo

    def create_event_reference_for_request(
        self, event_reference_request: EventReferenceRequest, rating: int = 50
    ) -> EventReference:
        existing_reference = self.repo.get_event_reference_by_event_id(
            event_reference_request.event_id,
            event_reference_request.admin_unit_id,
        )
        if existing_reference:  # pragma: no cover
            return existing_reference

        return self.repo.create_event_reference(
            event_id=event_reference_request.event_id,
            admin_unit_id=event_reference_request.admin_unit_id,
            rating=rating,
        )
