from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.oauth2_client_read_models import (
    OAuth2ClientReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListUserOAuth2ClientsQuery(Query[Page[OAuth2ClientReadModel]]):
    """OAuth2 clients of a user in id order; the actor must be that user."""

    user_id: ObjectId
    page: PageRequest = PageRequest()
