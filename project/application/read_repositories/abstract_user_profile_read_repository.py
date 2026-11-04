import abc
from typing import Optional

from project.application.read_models.user_profile_read_model import UserProfileReadModel
from project.domain.types.object_id import ObjectId


class AbstractUserProfileReadRepository(abc.ABC):
    @abc.abstractmethod
    def get_profile(
        self, user_id: ObjectId
    ) -> Optional[UserProfileReadModel]:  # pragma: no cover
        raise NotImplementedError
