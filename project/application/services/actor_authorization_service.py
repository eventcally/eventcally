from typing import Optional

from project.application.read_repositories.abstract_actor_permission_read_repository import (
    AbstractActorPermissionReadRepository,
)
from project.application.services.actor_permission_policy import (
    actor_can_use_planning,
    actor_has_permission_for_admin_unit,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from project.domain.translation import dummy_gettext
from project.domain.types.object_id import ObjectId


class ActorAuthorizationService:
    """Actor-based authorization for query handlers.

    Same rule as `authorization_utils` gives command handlers, answered on the
    read session.
    """

    def __init__(self, reader: AbstractActorPermissionReadRepository):
        self.reader = reader

    def has_permission_for_admin_unit(
        self, actor: Optional[Actor], admin_unit_id: ObjectId, permission: str
    ) -> bool:
        return actor_has_permission_for_admin_unit(
            actor, admin_unit_id, permission, self.reader
        )

    def can_use_planning(self, actor: Optional[Actor]) -> bool:
        return actor_can_use_planning(actor, self.reader)

    def ensure_is_user(self, actor: Optional[Actor], user_id: ObjectId):
        """The actor must *be* `user_id` (a user's own resources; no delegation)."""
        if actor is None or actor.user_id is None or actor.user_id != user_id:
            raise UnauthorizedError(f"Actor is not permitted to act as user {user_id}.")

    def is_recipient(self, actor: Optional[Actor], email: Optional[str]) -> bool:
        """Whether `email` (an invitation's address) is the actor's user email,
        ignoring case."""
        if actor is None or actor.user_id is None or not email:
            return False

        user_email = self.reader.user_email(actor.user_id)
        return user_email is not None and user_email.lower() == email.lower()

    def ensure_is_recipient(self, actor: Optional[Actor], email: Optional[str]):
        if not self.is_recipient(actor, email):
            raise UnauthorizedError(
                dummy_gettext(
                    "Actor is not permitted to perform this action on behalf of a user."
                )
            )

    def ensure_is_platform_admin(self, actor: Optional[Actor]):
        if (
            actor is None
            or actor.user_id is None
            or not self.reader.is_platform_admin(actor.user_id)
        ):
            raise UnauthorizedError(
                dummy_gettext(
                    "Actor is not permitted to perform this platform-admin action."
                )
            )

    def ensure_permission_for_admin_unit(
        self, actor: Optional[Actor], admin_unit_id: ObjectId, permission: str
    ):
        if not self.has_permission_for_admin_unit(actor, admin_unit_id, permission):
            raise UnauthorizedError(
                f"Actor is not permitted to perform '{permission}' "
                f"for admin unit {admin_unit_id}."
            )
