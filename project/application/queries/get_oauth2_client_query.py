from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.oauth2_client_read_models import (
    OAuth2ClientReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOAuth2ClientQuery(Query[Optional[OAuth2ClientReadModel]]):
    """`None` if the client does not exist. An organization's client requires
    `oauth2_clients:read` on it; a user's client requires the actor to be that
    user."""

    id: ObjectId
