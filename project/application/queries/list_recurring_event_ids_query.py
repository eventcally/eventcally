from typing import List

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ListRecurringEventIdsQuery(Query[List[ObjectId]]):
    """Events with a recurring date definition, by id. Selection for the nightly
    recurring-dates job; the refresh is done per event by
    `UpdateEventRecurringDatesCommand`."""

    pass
