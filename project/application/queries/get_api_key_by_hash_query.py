from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.api_key_read_models import ApiKeyReadModel


class GetApiKeyByHashQuery(Query[Optional[ApiKeyReadModel]]):
    """The API key with this key hash (API authentication), or `None`."""

    key_hash: str
