from project.application.queries.base import Query
from project.application.read_models.organization_export_read_models import (
    OrganizationExportReadModel,
)
from project.domain.types import ObjectId


class GetOrganizationExportQuery(Query[OrganizationExportReadModel]):
    """Requires `export:read` of the organization."""

    admin_unit_id: ObjectId
