from flask import abort
from flask_security import current_user
from flask_security.utils import FsPermNeed
from flask_principal import Permission
from project.models import AdminUnitMember, AdminUnit
from project.services.admin_unit import get_member_for_admin_unit_by_user_id


def has_current_user_permission(permission):
    user_perm = Permission(FsPermNeed(permission))
    return user_perm.can()


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


def can_request_event_reference(event):
    if not has_access(event.admin_unit, "reference_request:create"):
        return False

    return len(get_admin_units_for_event_reference_request(event)) > 0


def get_admin_units_for_event_reference_request(event):
    return AdminUnit.query.filter(AdminUnit.id != event.admin_unit_id).all()


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
