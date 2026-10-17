from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.oauth2_client_read_models import (
    OAuth2ClientReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOrganizationOAuth2ClientsQuery(Query[Optional[Page[OAuth2ClientReadModel]]]):
    """OAuth2 clients (not apps) of an organization in id order; `None` if the
    organization does not exist. Requires `oauth2_clients:read`."""

    admin_unit_id: ObjectId
    page: PageRequest = PageRequest()
