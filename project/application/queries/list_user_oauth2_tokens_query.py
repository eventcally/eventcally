from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.oauth2_token_read_models import (
    OAuth2TokenReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListUserOAuth2TokensQuery(Query[Page[OAuth2TokenReadModel]]):
    """Tokens of a user, newest first; the actor must be that user."""

    user_id: ObjectId
    page: PageRequest = PageRequest()
