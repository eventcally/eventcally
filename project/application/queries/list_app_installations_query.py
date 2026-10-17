from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppInstallationsQuery(Query[Optional[Page[AppInstallationReadModel]]]):
    """Apps installed by an organization in id order; `None` if the organization
    does not exist. Requires `app_installations:read`."""

    admin_unit_id: ObjectId
    page: PageRequest = PageRequest()
