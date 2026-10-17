from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_read_models import (
    OrganizationWidgetSettingsReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationWidgetSettingsQuery(
    Query[Optional[OrganizationWidgetSettingsReadModel]]
):
    """The public widget styles of an organization, or `None`."""

    id: ObjectId
