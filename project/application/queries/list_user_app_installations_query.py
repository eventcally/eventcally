from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_installation_read_models import (
    UserAppInstallationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListUserAppInstallationsQuery(Query[Page[UserAppInstallationReadModel]]):
    """Installations of `app_id` in organizations where `user_id` is a member
    (an admin with `admin_only`), in id order. The actor must be that user."""

    user_id: ObjectId
    app_id: ObjectId
    admin_only: bool = False
    page: PageRequest = PageRequest()
