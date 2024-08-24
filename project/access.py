from authlib.integrations.flask_oauth2 import current_token
from flask import abort
from flask_login import login_user
from flask_principal import Permission, RoleNeed
from flask_security import current_user
from flask_security.utils import FsPermNeed
from sqlalchemy import and_, exists

from project import app, db
from project.models import AdminUnit, AdminUnitMember, Event, PublicStatus, User
from project.models.admin_unit import AdminUnitMemberRole
from project.services.admin_unit import get_member_for_admin_unit_by_user_id


def has_current_user_permission(permission):
    user_perm = Permission(FsPermNeed(permission))
    return user_perm.can()


def has_current_user_role(role):
    user_perm = Permission(RoleNeed(role))
    return user_perm.can()


def has_owner_access(user_id):
    return user_id == current_user.id


def owner_access_or_401(user_id):
    if not has_owner_access(user_id):
        abort(401)
    return None


def login_api_user() -> bool:
    return (
        current_token
        and current_token.user
        and login_user(current_token.user)
        or current_user
        and current_user.is_authenticated
    )


def login_api_user_or_401() -> bool:
    if not login_api_user():
        abort(401)


def has_admin_unit_member_role(admin_unit_member, role_name):
    for role in admin_unit_member.roles:
        if role.name == role_name:
            return True
    return False


def has_admin_unit_member_permission(admin_unit_member, permission):
    for role in admin_unit_member.roles:
        if permission in role.get_permissions():
            return True
    return False


def get_current_user_member_for_admin_unit(admin_unit_id):
    return get_member_for_admin_unit_by_user_id(admin_unit_id, current_user.id)


def has_current_user_member_permission_for_admin_unit(admin_unit_id, permission):
    admin_unit_member = get_current_user_member_for_admin_unit(admin_unit_id)
    if admin_unit_member is not None:
        if has_admin_unit_member_permission(admin_unit_member, permission):
            return True
    return False


def has_current_user_member_role_for_admin_unit(admin_unit_id, role_name):
    admin_unit_member = get_current_user_member_for_admin_unit(admin_unit_id)
    if admin_unit_member is not None:
        if has_admin_unit_member_role(admin_unit_member, role_name):
            return True
    return False


def has_current_user_permission_for_admin_unit(admin_unit, permission):
    if not current_user.is_authenticated:
        return False

    if has_current_user_permission(permission):
        return True

    if has_current_user_member_permission_for_admin_unit(admin_unit.id, permission):
        return True

    return False


def has_access(admin_unit, permission):
    return has_current_user_permission_for_admin_unit(admin_unit, permission)


def access_or_401(admin_unit, permission):
    if not has_access(admin_unit, permission):
        abort(401)


def get_admin_units_with_current_user_permission(permission):
    result = list()

    admin_units = get_admin_units_for_manage()
    for admin_unit in admin_units:
        if has_current_user_permission_for_admin_unit(admin_unit, permission):
            result.append(admin_unit)

    return result


def can_reference_event(event):
    return len(get_admin_units_for_event_reference(event)) > 0


def get_admin_units_for_event_reference(event):
    result = list()

    admin_units = get_admin_units_with_current_user_permission("event:reference")
    for admin_unit in admin_units:
        if admin_unit.id != event.admin_unit_id:
            result.append(admin_unit)

    return result


def can_request_event_reference_from_admin_unit(admin_unit):
    if not has_access(admin_unit, "reference_request:create"):
        return False

    if not admin_unit.is_verified:
        return False

    return True


def can_request_event_reference(event):
    if not can_request_event_reference_from_admin_unit(event.admin_unit):
        return False

    if event.public_status != PublicStatus.published:
        return False

    return db.session.scalar(
        exists()
        .where(
            and_(
                AdminUnit.id != event.admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
        )
        .select()
    )


def admin_units_the_current_user_is_member_of():
    result = list()

    if current_user.is_authenticated:
        admin_unit_members = AdminUnitMember.query.filter_by(
            user_id=current_user.id
        ).all()
        for admin_unit_member in admin_unit_members:
            result.append(admin_unit_member.adminunit)

    return result


def get_admin_units_for_manage():
    # Global admin
    if current_user.has_role("admin"):
        return AdminUnit.query.all()

    return admin_units_the_current_user_is_member_of()


def get_admin_unit_for_manage(admin_unit_id):
    admin_units = get_admin_units_for_manage()
    return next((au for au in admin_units if au.id == admin_unit_id), None)


def get_admin_unit_for_manage_or_404(admin_unit_id):
    admin_unit = get_admin_unit_for_manage(admin_unit_id)

    if not admin_unit:
        abort(404)

    return admin_unit


def admin_unit_suggestions_enabled_or_404(admin_unit: AdminUnit):
    if not admin_unit.suggestions_enabled:
        abort(404)


def can_create_admin_unit():
    if not current_user.is_authenticated:  # pragma: no cover
        return False

    if not app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"]:
        return True

    if has_current_user_role("admin"):
        return True

    admin_units = get_admin_units_for_manage()
    return any(admin_unit.can_create_other for admin_unit in admin_units)


def can_use_planning():
    if not current_user.is_authenticated:
        return False

    if has_current_user_role("admin"):  # pragma: no cover
        return True

    return current_user.is_member_of_verified_admin_unit


def can_verify_admin_unit():
    if not current_user.is_authenticated:  # pragma: no cover
        return False

    if has_current_user_role("admin"):  # pragma: no cover
        return True

    admin_units = get_admin_units_for_manage()
    return any(admin_unit.can_verify_other for admin_unit in admin_units)


def can_read_event(event: Event) -> bool:
    if event.public_status == PublicStatus.published and event.admin_unit.is_verified:
        return True

    if (
        event.public_status == PublicStatus.planned
        and event.admin_unit.is_verified
        and can_use_planning()
    ):
        return True

    return has_access(event.admin_unit, "event:read")


def can_read_event_or_401(event: Event):
    if not can_read_event(event):
        abort(401)


def can_read_private_events(admin_unit: AdminUnit) -> bool:
    return has_access(admin_unit, "event:read")


def get_admin_unit_members_with_permission(admin_unit_id: int, permission: str) -> list:
    members = (
        AdminUnitMember.query.join(User)
        .filter(AdminUnitMember.admin_unit_id == admin_unit_id)
        .all()
    )

    return list(
        filter(
            lambda member: has_admin_unit_member_permission(member, permission), members
        )
    )


def can_current_user_delete_member(member: AdminUnitMember) -> bool:
    if current_user.has_role("admin"):  # pragma: no cover
        return True

    # Check if there is another admin
    return (
        AdminUnitMember.query.filter(
            AdminUnitMember.user_id != member.user_id,
            AdminUnitMember.admin_unit_id == member.admin_unit_id,
            AdminUnitMember.roles.any(AdminUnitMemberRole.name == "admin"),
        ).first()
        is not None
    )
