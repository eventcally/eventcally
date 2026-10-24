from authlib.integrations.flask_oauth2 import current_token
from flask import abort, current_app, g
from flask_security import current_user

from project.application.queries import (
    AnyOrganizationAcceptsReferenceRequestsQuery,
    GetCurrentOrganizationQuery,
    GetManageableOrganizationQuery,
    HasOtherAdminQuery,
    ListManageableOrganizationsQuery,
    ListUserOrganizationInvitationsQuery,
)
from project.application.queries.page_request import PageRequest
from project.application.read_models.organization_member_read_models import (
    UserOrganizationMembershipReadModel,
)
from project.domain.models.enums.event_public_status import EventPublicStatus


def has_owner_access(user_id):
    return user_id == current_user.id


def owner_access_or_401(user_id):
    if not has_owner_access(user_id):
        abort(401)
    return None


def login_api_user() -> bool:
    """Make the OAuth token's user the current user for this request only.
    The API never authenticates through the session cookie."""
    if current_token and current_token.user:
        g._login_user = current_token.user
        return True
    return False


def login_api_user_or_401() -> bool:
    if not login_api_user():
        abort(401)


def _query_bus():
    return current_app.container.cqrs.query_bus()


def _authorization():
    """The one permission policy, answered on the read session (released with the
    app context)."""
    return current_app.container.cqrs.actor_authorization_service()


def _current_actor():
    from project.shared.context import ContextProvider

    return ContextProvider().current_actor


def is_platform_admin() -> bool:
    actor = _current_actor()
    return actor.user_id is not None and _authorization().reader.is_platform_admin(
        actor.user_id
    )


def has_access(admin_unit, permission):
    """Whether the current actor (user or app installation) has `permission` for the
    organization; `admin_unit` only needs an `id`.

    A user who authenticated with an OAuth token has no platform-admin bypass here:
    the bypass was always tied to the session identity, so an admin's API token only
    reaches the organizations the admin is a member of (the query handlers apply the
    actor-based rule themselves)."""
    actor = _current_actor()
    authz = _authorization()

    if actor.user_id is not None and current_token and current_token.user:
        return authz.reader.member_has_permission(
            admin_unit.id, actor.user_id, permission
        )

    return authz.has_permission_for_admin_unit(actor, admin_unit.id, permission)


def access_or_401(admin_unit, permission):
    if not has_access(admin_unit, permission):  # pragma: no cover
        abort(401)


def has_admin_unit_owner_access(admin_unit_id):
    admin_unit = getattr(g, "manage_admin_unit", None)
    return admin_unit and (admin_unit_id == admin_unit.id)


def admin_unit_owner_access_or_401(admin_unit_id):
    if not has_admin_unit_owner_access(admin_unit_id):
        abort(401)
    return None


def get_admin_units_with_current_user_permission(permission):
    result = list()

    admin_units = get_admin_units_for_manage()
    for admin_unit in admin_units:
        if has_access(admin_unit, permission):
            result.append(admin_unit)

    return result


def get_admin_units_with_current_token_permission(permission):  # pragma: no cover
    result = list()

    if not current_token:
        return result

    if not current_token.app_installation:
        return result

    if permission not in current_token.app_installation.permissions:
        return result

    result.append(
        _query_bus().handle(
            GetCurrentOrganizationQuery(id=current_token.app_installation.admin_unit_id)
        )
    )
    return result


def get_admin_units_with_current_user_or_token_permission(permission):
    if current_user.is_authenticated:
        return get_admin_units_with_current_user_permission(permission)

    return get_admin_units_with_current_token_permission(permission)


def can_reference_event(event):
    return len(get_admin_units_for_event_reference(event)) > 0


def get_admin_units_for_event_reference(event):
    result = list()

    admin_units = get_admin_units_with_current_user_or_token_permission(
        "incoming_event_references:write"
    )
    for admin_unit in admin_units:
        if admin_unit.id != event.admin_unit_id:
            result.append(admin_unit)

    return result


def can_request_event_reference_from_admin_unit(admin_unit):
    if not has_access(admin_unit, "outgoing_event_reference_requests:write"):
        return False

    if not admin_unit.is_verified:
        return False

    return True


def can_request_event_reference(event):
    if not can_request_event_reference_from_admin_unit(event.admin_unit):
        return False

    if event.public_status != EventPublicStatus.published:
        return False

    return _query_bus().handle(
        AnyOrganizationAcceptsReferenceRequestsQuery(
            exclude_admin_unit_id=event.admin_unit_id
        )
    )


def admin_units_the_current_user_is_member_of():
    return _query_bus().handle(ListManageableOrganizationsQuery(member_only=True))


def get_admin_units_for_manage():
    return _query_bus().handle(ListManageableOrganizationsQuery())


def get_admin_unit_for_manage(admin_unit_id):
    return _query_bus().handle(GetManageableOrganizationQuery(id=admin_unit_id))


def get_admin_unit_for_manage_or_404(admin_unit_id):
    admin_unit = get_admin_unit_for_manage(admin_unit_id)

    if not admin_unit:
        if not current_user.is_authenticated:
            # Anonymous users following e.g. an email link should be sent to
            # login (with a `next` back to the original page), not shown a 404.
            abort(current_app.login_manager.unauthorized())
        abort(404)

    return admin_unit


def can_create_admin_unit():
    if not current_user.is_authenticated:  # pragma: no cover
        return False

    if not current_app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"]:
        return True

    if is_platform_admin():
        return True

    admin_units = get_admin_units_for_manage()
    return any(admin_unit.can_create_other for admin_unit in admin_units)


def can_use_planning():
    return _authorization().can_use_planning(_current_actor())


def _has_organization_invitation() -> bool:
    page = _query_bus().handle(
        ListUserOrganizationInvitationsQuery(
            user_id=current_user.id, page=PageRequest(per_page=1)
        )
    )
    return bool(page.items)


def can_use_manage_place_lookup():
    """The Google place lookup of the location filters and forms: planning users,
    every member of an organization (the manage event list) and users who can create
    an organization (the first one has no membership yet) or were invited to one."""
    return (
        can_use_planning()
        or bool(get_admin_units_for_manage())
        or can_create_admin_unit()
        or _has_organization_invitation()
    )


def can_verify_admin_unit_user():
    if not current_user.is_authenticated:  # pragma: no cover
        return False

    if is_platform_admin():  # pragma: no cover
        return True

    admin_units = get_admin_units_for_manage()
    return any(admin_unit.can_verify_other for admin_unit in admin_units)


def can_verify_admin_unit_token():
    if not current_token:  # pragma: no cover
        return False

    if not current_token.app_installation:
        return False

    organization = _query_bus().handle(
        GetCurrentOrganizationQuery(id=current_token.app_installation.admin_unit_id)
    )
    return organization.can_verify_other


def can_verify_admin_unit():
    return can_verify_admin_unit_user() or can_verify_admin_unit_token()


def can_current_user_delete_member(member: UserOrganizationMembershipReadModel) -> bool:
    if is_platform_admin():  # pragma: no cover
        return True

    # Check if there is another admin
    return _query_bus().handle(
        HasOtherAdminQuery(admin_unit_id=member.admin_unit_id, user_id=member.user_id)
    )
