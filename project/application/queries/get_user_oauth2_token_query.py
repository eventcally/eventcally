from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.oauth2_token_read_models import (
    OAuth2TokenReadModel,
)
from project.domain.types.object_id import ObjectId


class GetUserOAuth2TokenQuery(Query[Optional[OAuth2TokenReadModel]]):
    """`None` if the token does not exist; the actor must be its user."""

    id: ObjectId
