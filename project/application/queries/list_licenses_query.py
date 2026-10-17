from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.image_read_model import LicenseRefReadModel
from project.application.read_models.page import Page


class ListLicensesQuery(Query[Page[LicenseRefReadModel]]):
    """All image licenses in id order (public)."""

    page: PageRequest = PageRequest()
