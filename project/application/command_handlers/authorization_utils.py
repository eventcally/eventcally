from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from project.domain.types import ObjectId


def has_actor_permission_for_admin_unit(
    actor: Actor, admin_unit_id: ObjectId, permission: str, uow: AbstractUnitOfWork
) -> bool:
    """Check `actor`'s permission against `admin_unit_id` from the actor's own
    identity, not from request-bound state (Flask-Login's `current_user`,
    Authlib's `current_token`) — so this works identically whether the
    command came from a view, an API request, or something dispatching the
    command directly with no HTTP request at all.

    Covers the two cases `Actor` can represent: an `AdminUnitMember`'s role
    permissions (with a platform-admin bypass, mirroring
    `has_current_user_role("admin")` in `project/access.py` — `UserAggregate.
    is_platform_admin` is this check's domain-layer equivalent), or an app
    installation's granted permissions.
    """
    if actor.user_id is not None:
        user = uow.users.get(actor.user_id)
        if user is not None and user.is_platform_admin:
            return True

        members = uow.organization_members.get_all_with_permission(
            admin_unit_id, permission
        )
        return any(member.user_id == actor.user_id for member in members)

    if actor.app_installation_id is not None:
        installation = uow.organization_app_installations.get(actor.app_installation_id)
        return (
            installation is not None
            and installation.admin_unit_id == admin_unit_id
            and permission in installation.permissions
        )

    return False


def ensure_actor_has_permission_for_admin_unit(
    actor: Actor, admin_unit_id: ObjectId, permission: str, uow: AbstractUnitOfWork
):
    if not has_actor_permission_for_admin_unit(actor, admin_unit_id, permission, uow):
        raise UnauthorizedError(
            f"Actor is not permitted to perform '{permission}' "
            f"for admin unit {admin_unit_id}."
        )


def ensure_actor_is_authenticated_user(actor: Actor, uow: AbstractUnitOfWork):
    """Guard for actions that have no admin unit to check a permission
    against, but that act *as* the user — creating a resource the actor is
    then made a member of, say. `Actor` can also represent an app
    installation (`user_id is None`), which has no user to own the result,
    so those actions must be refused rather than silently persisting a
    member row without a user."""
    user = uow.users.get(actor.user_id) if actor.user_id is not None else None

    if user is None:
        raise UnauthorizedError(
            "Actor is not permitted to perform this action on behalf of a user."
        )

    return user


def ensure_actor_is_user(actor: Actor, user_id: ObjectId):
    """Guard for a user-owned resource: the actor must *be* `user_id`, not
    merely act on its behalf — there is no delegation or platform-admin
    bypass for a user's own resources, unlike admin-unit permissions."""
    if actor.user_id != user_id:
        raise UnauthorizedError(f"Actor is not permitted to act as user {user_id}.")


def ensure_actor_is_platform_admin(actor: Actor, uow: AbstractUnitOfWork):
    """Guard for platform-admin-only actions (the admin backoffice). No
    admin-unit-membership or app-installation fallback — being a member
    with e.g. settings:write on some org must never satisfy this."""
    user = uow.users.get(actor.user_id) if actor.user_id is not None else None
    if user is None or not user.is_platform_admin:
        raise UnauthorizedError(
            "Actor is not permitted to perform this platform-admin action."
        )
