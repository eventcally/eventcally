from typing import List

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ListUserIdsDueForDeletionQuery(Query[List[ObjectId]]):
    """Users whose deletion was requested more than three days ago. Selection for the cleanup jobs; the deletions are done by the job."""

    pass
