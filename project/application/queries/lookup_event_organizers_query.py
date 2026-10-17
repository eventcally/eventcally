from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerRefReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class LookupEventOrganizersQuery(Query[Page[EventOrganizerRefReadModel]]):
    """Select2 lookup: organizers of the organization whose name matches `term`."""

    admin_unit_id: ObjectId
    term: Optional[str] = None
    page: PageRequest = PageRequest()
