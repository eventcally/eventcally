from typing import List

from pydantic import Field

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import (
    DumpEventReferenceReadModel,
)


class ListDumpEventReferencesQuery(Query[List[DumpEventReferenceReadModel]]):
    """One keyset batch of event references for the data dumps."""

    after_id: int = Field(default=0, ge=0)
    limit: int = Field(default=200, ge=1, le=1000)
