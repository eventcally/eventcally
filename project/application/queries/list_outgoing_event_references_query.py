from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.event_reference_read_models import (
    EventReferenceReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOutgoingEventReferencesQuery(Query[Optional[Page[EventReferenceReadModel]]]):
    """References of the organization's events by others, newest first; `None` if
    the organization does not exist. Requires `outgoing_event_references:read`."""

    admin_unit_id: ObjectId
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
