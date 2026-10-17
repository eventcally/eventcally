from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.oauth2_client_read_models import AppReadModel
from project.domain.types.object_id import ObjectId


class GetAppQuery(Query[Optional[AppReadModel]]):
    """`None` if no app (an OAuth2 client with app permissions) has this id.
    Requires `apps:read` on the app's organization."""

    id: ObjectId
