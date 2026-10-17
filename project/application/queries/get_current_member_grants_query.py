from project.application.queries.base import Query
from project.application.read_models.access_helper_read_models import (
    MemberGrantsReadModel,
)
from project.domain.types.object_id import ObjectId


class GetCurrentMemberGrantsQuery(Query[MemberGrantsReadModel]):
    """The actor's own roles and permissions in the organization (empty for
    non-members and actors without a user)."""

    admin_unit_id: ObjectId
