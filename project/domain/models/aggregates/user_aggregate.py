from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.types.object_id import ObjectId


class UserAggregate(BaseAggregate):
    id: ObjectId
    email: str
    locale: Optional[str]
