from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetAppInstallationQuery(Query[Optional[AppInstallationReadModel]]):
    """`None` if the installation does not exist. Requires
    `app_installations:read` on the installing organization."""

    id: ObjectId
