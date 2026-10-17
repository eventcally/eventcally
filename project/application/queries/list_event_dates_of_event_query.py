from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import EventDateListItemReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListEventDatesOfEventQuery(Query[Optional[Page[EventDateListItemReadModel]]]):
    """The dates of an event by start; `None` if the event is unknown. Authorizes like
    `GetEventDetailQuery`."""

    event_id: ObjectId
    page: PageRequest = PageRequest()
