from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_installation_read_models import (
    InstallableAppReadModel,
)
from project.domain.types.object_id import ObjectId


class GetInstallableAppQuery(Query[Optional[InstallableAppReadModel]]):
    """An app's public install information, or `None` if no app has this id."""

    id: ObjectId
