from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOutgoingOrganizationRelationByTargetQuery(
    Query[Optional[OrganizationRelationReadModel]]
):
    """The relation of `admin_unit_id` to `target_admin_unit_id`, or `None`.
    Requires `outgoing_organization_relations:read` on `admin_unit_id`."""

    admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
