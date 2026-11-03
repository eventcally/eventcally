from typing import Optional

from sqlalchemy import select

from project.application.read_models.user_profile_read_model import UserProfileReadModel
from project.application.read_repositories.abstract_user_profile_read_repository import (
    AbstractUserProfileReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import User


class SqlAlchemyUserProfileReadRepository(AbstractUserProfileReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_profile(self, user_id: ObjectId) -> Optional[UserProfileReadModel]:
        user = self.session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if user is None:
            return None

        return UserProfileReadModel(
            id=user.id,
            email=user.email,
            locale=user.locale,
            newsletter_enabled=bool(user.newsletter_enabled),
            deletion_requested_at=user.deletion_requested_at,
            tos_accepted_at=user.tos_accepted_at,
        )
