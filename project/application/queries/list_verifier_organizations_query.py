from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import (
    VerifierOrganizationReadModel,
)
from project.application.read_models.page import Page


class ListVerifierOrganizationsQuery(Query[Page[VerifierOrganizationReadModel]]):
    """Organizations that verify others and serve `postal_code`, by name."""

    postal_code: str
    page: PageRequest = PageRequest()
