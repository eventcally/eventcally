from typing import Optional

from project.application.read_repositories.abstract_actor_permission_read_repository import (
    AbstractActorPermissionReadRepository,
)
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


def actor_has_permission_for_admin_unit(
    actor: Optional[Actor],
    admin_unit_id: ObjectId,
    permission: str,
    reader: AbstractActorPermissionReadRepository,
) -> bool:
    """Check `actor`'s permission against `admin_unit_id` from the actor's own
    identity, not from request-bound state (Flask-Login's `current_user`,
    Authlib's `current_token`) — so this works identically whether the
    command or query came from a view, an API request, or something
    dispatching it directly with no HTTP request at all.

    Covers the two cases `Actor` can represent: an `AdminUnitMember`'s role
    permissions (with a platform-admin bypass, mirroring
    `has_current_user_role("admin")` in `project/presentation/shared/access.py` — `UserAggregate.
    is_platform_admin` is this check's domain-layer equivalent), or an app
    installation's granted permissions. A user actor never falls through to
    the installation branch.

    This is the single rule for commands (answered through a unit of work)
    and queries (answered through a read repository on the read session).
    """
    if actor is None:
        return False

    if actor.user_id is not None:
        if reader.is_platform_admin(actor.user_id):
            return True

        return reader.member_has_permission(admin_unit_id, actor.user_id, permission)

    if actor.app_installation_id is not None:
        return reader.installation_has_permission(
            actor.app_installation_id, admin_unit_id, permission
        )

    return False


def actor_can_use_planning(
    actor: Optional[Actor], reader: AbstractActorPermissionReadRepository
) -> bool:
    """Mirrors `access.can_use_planning`: platform admins and members of a verified
    organization, or an installation of a verified organization."""
    if actor is None:
        return False

    if actor.user_id is not None:
        return reader.is_platform_admin(
            actor.user_id
        ) or reader.is_member_of_verified_organization(actor.user_id)

    if actor.app_installation_id is not None:
        return reader.installation_organization_is_verified(actor.app_installation_id)

    return False
