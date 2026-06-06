from __future__ import annotations

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.types.object_id import ObjectId


class OrganisationMemberAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    user_id: ObjectId
