from project import db
from project.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitMemberRole,
    EventOrganizer,
    Location,
)
from project.services.location import assign_location_values
from project.views.utils import upsert_image_with_data


def insert_admin_unit_for_user(admin_unit, user):
    db.session.add(admin_unit)

    # Nutzer als Admin hinzufügen
    add_user_to_admin_unit_with_roles(user, admin_unit, ["admin", "event_verifier"])
    db.session.commit()

    # Organizer anlegen
    organizer = EventOrganizer()
    organizer.admin_unit_id = admin_unit.id
    organizer.name = admin_unit.name
    organizer.url = admin_unit.url
    organizer.email = admin_unit.email
    organizer.phone = admin_unit.phone
    organizer.fax = admin_unit.fax
    organizer.location = Location()
    assign_location_values(organizer.location, admin_unit.location)
    if admin_unit.logo:
        organizer.logo = upsert_image_with_data(
            organizer.logo,
            admin_unit.logo.data,
            admin_unit.logo.encoding_format,
        )
    db.session.add(organizer)
    db.session.commit()


def get_admin_unit_by_id(id):
    return AdminUnit.query.filter_by(id=id).first()


def get_admin_unit_by_name(unit_name):
    return AdminUnit.query.filter_by(name=unit_name).first()


def get_admin_unit_member_role(role_name):
    return AdminUnitMemberRole.query.filter_by(name=role_name).first()


def upsert_admin_unit_member_role(role_name, role_title, permissions):
    result = AdminUnitMemberRole.query.filter_by(name=role_name).first()
    if result is None:
        result = AdminUnitMemberRole(name=role_name)
        db.session.add(result)

    result.title = role_title
    result.remove_permissions(result.get_permissions())
    result.add_permissions(permissions)
    return result


def add_user_to_admin_unit(user, admin_unit):
    result = (
        AdminUnitMember.query.with_parent(admin_unit).filter_by(user_id=user.id).first()
    )
    if result is None:
        result = AdminUnitMember(user=user, admin_unit_id=admin_unit.id)
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
        if not role:
            raise ValueError("Role %s does not exist" % role_name)
        add_role_to_admin_unit_member(member, role)


def add_role_to_admin_unit_member(admin_unit_member, role):
    if (
        AdminUnitMemberRole.query.with_parent(admin_unit_member)
        .filter_by(name=role.name)
        .first()
        is None
    ):
        admin_unit_member.roles.append(role)


def get_member_for_admin_unit_by_user_id(admin_unit_id, user_id):
    return AdminUnitMember.query.filter_by(
        admin_unit_id=admin_unit_id, user_id=user_id
    ).first()


def get_admin_unit_member(id):
    return AdminUnitMember.query.filter_by(id=id).first()
