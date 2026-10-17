from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.app_child_read_models import AppKeyReadModel
from project.domain.types.object_id import ObjectId


class GetAppKeyQuery(Query[Optional[AppKeyReadModel]]):
    """`None` if the key does not exist. Requires `app_keys:read` on its
    organization."""

    id: ObjectId
