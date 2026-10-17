from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.app_installation_read_models import (
    AppInstallationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppInstallationsForAppQuery(Query[Page[AppInstallationReadModel]]):
    """Installations of `app_id` in id order. `app_id` is the authenticated app
    itself (app token), so there is nothing further to authorize."""

    app_id: ObjectId
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
