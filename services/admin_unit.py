from app import db
from models import AdminUnit, AdminUnitMember, AdminUnitMemberRole

def upsert_admin_unit(unit_name, short_name = None):
    admin_unit = AdminUnit.query.filter_by(name = unit_name).first()
    if admin_unit is None:
        admin_unit = AdminUnit(name = unit_name)
        db.session.add(admin_unit)

    admin_unit.short_name = short_name
    upsert_org_or_admin_unit_for_admin_unit(admin_unit)
    return admin_unit

def get_admin_unit(unit_name):
    return AdminUnit.query.filter_by(name = unit_name).first()

def get_admin_unit_member_role(role_name):
    return AdminUnitMemberRole.query.filter_by(name = role_name).first()

def upsert_admin_unit_member_role(role_name, role_title, permissions):
    result = AdminUnitMemberRole.query.filter_by(name = role_name).first()
    if result is None:
        result = AdminUnitMemberRole(name = role_name)
        db.session.add(result)

    result.title = role_title
    result.remove_permissions(result.get_permissions())
    result.add_permissions(permissions)
    return result

def add_user_to_admin_unit(user, admin_unit):
    result = AdminUnitMember.query.with_parent(admin_unit).filter_by(user_id = user.id).first()
    if result is None:
        result = AdminUnitMember(user = user, admin_unit_id=admin_unit.id)
        admin_unit.members.append(result)
        db.session.add(result)
    return result

def add_user_to_admin_unit_with_roles(user, admin_unit, role_names):
    member = add_user_to_admin_unit(user, admin_unit)
    add_roles_to_admin_unit_member(member, role_names)

    return member

def add_roles_to_admin_unit_member(member, role_names):
    for role_name in role_names:
        role = get_admin_unit_member_role(role_name)
        add_role_to_admin_unit_member(member, role)

def add_role_to_admin_unit_member(admin_unit_member, role):
    if AdminUnitMemberRole.query.with_parent(admin_unit_member).filter_by(name = role.name).first() is None:
        admin_unit_member.roles.append(role)
