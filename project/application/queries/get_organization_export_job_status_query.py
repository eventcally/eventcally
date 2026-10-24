from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_export_read_models import (
    OrganizationExportJobStatusReadModel,
)
from project.domain.types import ObjectId


class GetOrganizationExportJobStatusQuery(
    Query[Optional[OrganizationExportJobStatusReadModel]]
):
    """Requires `export:read`. `None` for job ids that do not belong to the
    organization."""

    admin_unit_id: ObjectId
    job_id: str
