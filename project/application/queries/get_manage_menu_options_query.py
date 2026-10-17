from project.application.queries.base import Query
from project.application.read_models.access_helper_read_models import (
    ManageMenuOptionsReadModel,
)
from project.domain.types.object_id import ObjectId


class GetManageMenuOptionsQuery(Query[ManageMenuOptionsReadModel]):
    """Inbox badge counts for the manage bar; zero unless the actor manages the
    organization (member or platform admin)."""

    admin_unit_id: ObjectId
