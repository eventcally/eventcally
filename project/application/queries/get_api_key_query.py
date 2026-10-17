from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.domain.types.object_id import ObjectId


class GetApiKeyQuery(Query[Optional[ApiKeyReadModel]]):
    """`None` if the key does not exist. An organization's key requires
    `api_keys:read` on it; a user's key requires the actor to be that user."""

    id: ObjectId
