from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.current_organization_read_models import (
    OrganizationSettingsReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationSettingsQuery(Query[Optional[OrganizationSettingsReadModel]]):
    """The organization with everything its settings forms show, or `None`. Only for
    actors who manage the organization (platform admin or member)."""

    id: ObjectId
