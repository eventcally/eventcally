from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.user_profile_read_model import UserProfileReadModel
from project.domain.types.object_id import ObjectId


class GetUserProfileQuery(Query[Optional[UserProfileReadModel]]):
    """The user's own profile, or `None`. The actor must be that user."""

    user_id: ObjectId
