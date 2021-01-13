from project import db
from project.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitMemberRole,
    AdminUnitMemberInvitation,
    EventOrganizer,
    EventPlace,
    Location,
)
from project.services.location import assign_location_values
from project.services.image import upsert_image_with_data
from sqlalchemy import func, and_, or_


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


def find_admin_unit_member_invitation(email, admin_unit_id):
    return AdminUnitMemberInvitation.query.filter(
        and_(
            AdminUnitMemberInvitation.admin_unit_id == admin_unit_id,
            AdminUnitMemberInvitation.email == email,
        )
    ).first()


def insert_admin_unit_member_invitation(admin_unit_id, email, role_names):
    invitation = AdminUnitMemberInvitation()
    invitation.admin_unit_id = admin_unit_id
    invitation.email = email
    invitation.roles = ",".join(role_names)
    db.session.add(invitation)
    db.session.commit()
    return invitation


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
            continue
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


def get_admin_unit_query(keyword=None):
    query = AdminUnit.query

    if keyword:
        like_keyword = "%" + keyword + "%"
        keyword_filter = or_(
            AdminUnit.name.ilike(like_keyword),
            AdminUnit.short_name.ilike(like_keyword),
        )
        query = query.filter(keyword_filter)

    return query.order_by(func.lower(AdminUnit.name))


def get_organizer_query(admin_unit_id, name=None):
    query = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        query = query.filter(EventOrganizer.name.ilike(like_name))

    return query.order_by(func.lower(EventOrganizer.name))


def get_place_query(admin_unit_id, name=None):
    query = EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        query = query.filter(EventPlace.name.ilike(like_name))

    return query.order_by(func.lower(EventPlace.name))
