"""ORM helpers for fixtures only: the Playwright seeding CLI (`project/cli/test.py`)
and the test seeders. Never import this from views, API, application or domain code;
production code goes through commands and queries."""

import base64
import time

from sqlalchemy import and_, func, update
from werkzeug.security import gen_salt

from project.extensions import db
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitMemberInvitation,
    AdminUnitMemberRole,
    AdminUnitRelation,
    AppKey,
    EventCategory,
    EventOrganizer,
    EventPlace,
    Image,
    Location,
    OAuth2Client,
    User,
)


def assign_location_values(target, origin):
    if origin:
        target.street = origin.street
        target.postalCode = origin.postalCode
        target.city = origin.city
        target.state = origin.state
        target.country = origin.country
        target.latitude = origin.latitude
        target.longitude = origin.longitude


def upsert_image_with_data(image, data, encoding_format="image/jpeg"):
    if image is None:
        image = Image()

    image.data = data
    image.encoding_format = encoding_format
    image.copyright_text = "EventCally"

    return image


def upsert_image_with_base64_str(image, base64_str, encoding_format):
    data = base64.b64decode(base64_str)
    return upsert_image_with_data(image, data, encoding_format)


def get_event_organizer(admin_unit_id, name):
    return EventOrganizer.query.filter(
        and_(EventOrganizer.name == name, EventOrganizer.admin_unit_id == admin_unit_id)
    ).first()


def upsert_event_organizer(admin_unit_id, name):
    result = get_event_organizer(admin_unit_id, name)
    if result is None:
        result = EventOrganizer(name=name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result


def get_event_place(admin_unit_id, name):
    return EventPlace.query.filter(
        and_(
            EventPlace.name == name,
            EventPlace.admin_unit_id == admin_unit_id,
        )
    ).first()


def upsert_event_place(admin_unit_id, name):
    result = get_event_place(admin_unit_id, name)
    if result is None:
        result = EventPlace(name=name, admin_unit_id=admin_unit_id)
        result.location = Location()
        db.session.add(result)

    return result


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

    # Place anlegen
    place = None
    if admin_unit.location:
        place = EventPlace()
        place.admin_unit_id = admin_unit.id
        place.name = admin_unit.location.city
        place.location = Location()
        assign_location_values(place.location, admin_unit.location)
        db.session.add(place)

    db.session.commit()

    return (organizer, place)


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
            func.lower(AdminUnitMemberInvitation.email) == func.lower(email),
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


def insert_admin_unit_relation(source_admin_unit_id: int, target_admin_unit_id: int):
    result = AdminUnitRelation(
        source_admin_unit_id=source_admin_unit_id,
        target_admin_unit_id=target_admin_unit_id,
    )
    db.session.add(result)
    return result


def get_admin_unit_relation(source_admin_unit_id: int, target_admin_unit_id: int):
    return AdminUnitRelation.query.filter_by(
        source_admin_unit_id=source_admin_unit_id,
        target_admin_unit_id=target_admin_unit_id,
    ).first()


def delete_admin_unit(admin_unit: AdminUnit):
    db.session.delete(admin_unit)
    db.session.commit()


def upsert_admin_unit_relation(source_admin_unit_id: int, target_admin_unit_id: int):
    result = get_admin_unit_relation(source_admin_unit_id, target_admin_unit_id)

    if result is None:
        result = insert_admin_unit_relation(source_admin_unit_id, target_admin_unit_id)

    return result


def upsert_event_category(category_name) -> EventCategory:
    category = EventCategory.query.filter_by(name=category_name).first()

    if category is None:
        category = EventCategory(name=category_name)
        db.session.add(category)
        db.session.commit()

    return category


def get_event_category(category_name):
    return EventCategory.query.filter_by(name=category_name).first()


def reset_tos_accepted_for_users():
    db.session.execute(update(User).values(tos_accepted_at=None))
    db.session.commit()


def complete_oauth2_client(oauth2_client: OAuth2Client) -> None:
    if not oauth2_client.id:
        oauth2_client.client_id = gen_salt(24)
        oauth2_client.client_id_issued_at = int(time.time())

    if oauth2_client.client_secret is None:
        oauth2_client.client_secret = gen_salt(48)


def add_keypair_to_oauth2_client(oauth2_client: OAuth2Client) -> tuple[bytes, AppKey]:
    app_key = AppKey()
    app_key.admin_unit_id = oauth2_client.admin_unit_id
    private_pem = app_key.generate_key()

    oauth2_client.app_keys.append(app_key)

    return (private_pem, app_key)
