from typing import List

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ListGhostUserIdsQuery(Query[List[ObjectId]]):
    """Users created more than 31 days ago who never confirmed. Selection for the cleanup jobs; the deletions are done by the job."""

    pass
