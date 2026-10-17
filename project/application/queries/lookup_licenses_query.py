from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.image_read_model import LicenseRefReadModel
from project.application.read_models.page import Page


class LookupLicensesQuery(Query[Page[LicenseRefReadModel]]):
    """Select2 lookup: licenses whose code or name match `term`, in `sort` order."""

    term: Optional[str] = None
    page: PageRequest = PageRequest()
