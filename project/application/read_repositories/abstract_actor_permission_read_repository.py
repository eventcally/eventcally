import abc
from typing import Optional

from project.domain.types.object_id import ObjectId


class AbstractActorPermissionReadRepository(abc.ABC):
    """Narrow questions about an actor's grants.

    The answers are facts; the decision lives in `actor_permission_policy`.
    """

    @abc.abstractmethod
    def is_platform_admin(self, user_id: ObjectId) -> bool:  # pragma: no cover
        """False for an unknown user."""
        raise NotImplementedError

    @abc.abstractmethod
    def member_has_permission(
        self, admin_unit_id: ObjectId, user_id: ObjectId, permission: str
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def installation_has_permission(
        self, app_installation_id: ObjectId, admin_unit_id: ObjectId, permission: str
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def user_email(self, user_id: ObjectId) -> Optional[str]:  # pragma: no cover
        """None for an unknown user."""
        raise NotImplementedError

    def is_member_of_verified_organization(
        self, user_id: ObjectId
    ) -> bool:  # pragma: no cover
        """Query side only (planning access); commands never ask."""
        raise NotImplementedError

    def installation_organization_is_verified(
        self, app_installation_id: ObjectId
    ) -> bool:  # pragma: no cover
        """Query side only (planning access); commands never ask."""
        raise NotImplementedError
