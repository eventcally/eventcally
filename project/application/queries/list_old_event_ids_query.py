from typing import List

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ListOldEventIdsQuery(Query[List[ObjectId]]):
    """Events that ended and were last modified more than 366 days ago. Selection for the cleanup jobs; the deletions are done by the job."""

    pass
