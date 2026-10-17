"""Shared fakes for query handler authorization tests."""

from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.models.entities.actor import Actor
from tests.application.services.test_actor_permission_policy import (
    FakeActorPermissionReader,
)

ACTOR = Actor(user_id=7)
ADMIN_UNIT_ID = 7


class SpyAuthorizationService(ActorAuthorizationService):
    def __init__(self, reader):
        super().__init__(reader)
        self.ensured = []

    def ensure_permission_for_admin_unit(self, actor, admin_unit_id, permission):
        self.ensured.append((actor, admin_unit_id, permission))
        super().ensure_permission_for_admin_unit(actor, admin_unit_id, permission)

    def ensure_is_user(self, actor, user_id):
        self.ensured.append((actor, "user", user_id))
        super().ensure_is_user(actor, user_id)

    def ensure_is_platform_admin(self, actor):
        self.ensured.append((actor, "platform_admin"))
        super().ensure_is_platform_admin(actor)


def authz(*permissions, admin_unit_id=ADMIN_UNIT_ID, user_id=7, admins=()):
    """Grants `user_id` the given permissions on `admin_unit_id`."""
    members = [(admin_unit_id, user_id, permission) for permission in permissions]
    return SpyAuthorizationService(
        FakeActorPermissionReader(members=members, admins=admins)
    )
