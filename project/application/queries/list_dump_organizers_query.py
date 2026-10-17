from typing import List, Optional

from pydantic import Field

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import DumpOrganizerReadModel
from project.domain.types.object_id import ObjectId


class ListDumpOrganizersQuery(Query[List[DumpOrganizerReadModel]]):
    """One keyset batch of organizers for the data dumps."""

    admin_unit_id: Optional[ObjectId] = None
    after_id: int = Field(default=0, ge=0)
    limit: int = Field(default=200, ge=1, le=1000)
