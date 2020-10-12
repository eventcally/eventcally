from flask_security import current_user
from flask_security.utils import FsPermNeed
from flask_principal import Permission
from models import AdminUnitMember, AdminUnit

def has_current_user_permission(permission):
    user_perm = Permission(FsPermNeed(permission))
    return user_perm.can()

def has_admin_unit_member_permission(admin_unit_member, permission):
    for role in admin_unit_member.roles:
        if permission in role.get_permissions():
            return True
    return False

def has_current_user_member_permission_for_admin_unit(admin_unit_id, permission):
    admin_unit_member = AdminUnitMember.query.filter_by(admin_unit_id=admin_unit_id, user_id=current_user.id).first()
    if admin_unit_member is not None:
        if has_admin_unit_member_permission(admin_unit_member, permission):
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

def can_list_admin_unit_members(admin_unit):
    return has_current_user_permission_for_admin_unit(admin_unit, 'admin_unit.members:read')

def can_create_event(admin_unit):
    return has_current_user_permission_for_admin_unit(admin_unit, 'event:create')

def can_update_event(event):
    return has_current_user_permission_for_admin_unit(event.admin_unit, 'event:update')

def can_delete_event(event):
    return has_current_user_permission_for_admin_unit(event.admin_unit, 'event:delete')

def can_reference_event(event):
    return len(get_admin_units_for_event_reference(event)) > 0

def can_update_organizer(organizer):
    return get_admin_unit_for_manage(organizer.admin_unit_id) is not None

def can_create_admin_unit():
    return current_user.is_authenticated

def can_verify_event_for_admin_unit(admin_unit):
    return has_current_user_permission_for_admin_unit(admin_unit, 'event:verify')

def can_verify_event(event):
    return can_verify_event_for_admin_unit(event.admin_unit)

def get_admin_units_with_current_user_permission(permission):
    result = list()

    admin_units = get_admin_units_for_manage()
    for admin_unit in admin_units:
        if has_current_user_permission_for_admin_unit(admin_unit, permission):
            result.append(admin_unit)

    return result

def get_admin_units_for_event_reference(event):
    result = list()

    admin_units = get_admin_units_with_current_user_permission('event:reference')
    for admin_unit in admin_units:
        if admin_unit.id != event.admin_unit_id:
            result.append(admin_unit)

    return result

def admin_units_the_current_user_is_member_of():
    result = list()

    if current_user.is_authenticated:
        admin_unit_members = AdminUnitMember.query.filter_by(user_id=current_user.id).all()
        for admin_unit_member in admin_unit_members:
            result.append(admin_unit_member.adminunit)

    return result

def get_admin_units_for_manage():
    # Global admin
    if current_user.has_role('admin'):
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