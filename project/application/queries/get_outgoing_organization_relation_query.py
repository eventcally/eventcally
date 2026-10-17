from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOutgoingOrganizationRelationQuery(
    Query[Optional[OrganizationRelationReadModel]]
):
    """`None` if the relation does not exist. Requires
    `outgoing_organization_relations:read` on the source organization."""

    id: ObjectId
