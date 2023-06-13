import datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import joinedload, load_only

from project import db
from project.models import (
    AdminUnit,
    AdminUnitInvitation,
    AdminUnitMember,
    AdminUnitMemberInvitation,
    AdminUnitMemberRole,
    AdminUnitRelation,
    CustomWidget,
    EventEventLists,
    EventList,
    EventOrganizer,
    EventPlace,
    Location,
)
from project.services.image import upsert_image_with_data
from project.services.location import assign_location_values


def insert_admin_unit_for_user(admin_unit, user, invitation=None):
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

    # Beziehung anlegen
    relation = None
    if invitation:
        inviting_admin_unit = get_admin_unit_by_id(invitation.admin_unit_id)
        relation = upsert_admin_unit_relation(invitation.admin_unit_id, admin_unit.id)
        relation.invited = True

        relation.auto_verify_event_reference_requests = (
            inviting_admin_unit.incoming_reference_requests_allowed
            and invitation.relation_auto_verify_event_reference_requests
        )
        relation.verify = (
            inviting_admin_unit.can_verify_other and invitation.relation_verify
        )

    db.session.commit()

    return (organizer, place, relation)


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


def get_admin_unit_member_invitations(email):
    return AdminUnitMemberInvitation.query.filter(
        func.lower(AdminUnitMemberInvitation.email) == func.lower(email)
    ).all()


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
    result.permissions = permissions
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


def get_admin_unit_query(
    keyword=None,
    include_unverified=False,
    only_verifier=False,
):
    query = AdminUnit.query

    if not include_unverified:
        query = query.filter(AdminUnit.is_verified)

    if only_verifier:
        only_verifier_filter = and_(
            AdminUnit.can_verify_other, AdminUnit.incoming_verification_requests_allowed
        )
        query = query.filter(only_verifier_filter)

    if keyword:
        like_keyword = "%" + keyword + "%"
        order_keyword = keyword + "%"
        keyword_filter = or_(
            AdminUnit.name.ilike(like_keyword),
            AdminUnit.short_name.ilike(like_keyword),
        )
        query = query.filter(keyword_filter).order_by(
            AdminUnit.name.ilike(order_keyword).desc(),
            AdminUnit.short_name.ilike(order_keyword).desc(),
            func.lower(AdminUnit.name),
        )
    else:
        query = query.order_by(func.lower(AdminUnit.name))

    return query


def get_organizer_query(admin_unit_id, name=None):
    query = EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        order_name = name + "%"
        query = query.filter(EventOrganizer.name.ilike(like_name)).order_by(
            EventOrganizer.name.ilike(order_name).desc(),
            func.lower(EventOrganizer.name),
        )
    else:
        query = query.order_by(func.lower(EventOrganizer.name))

    return query


def get_custom_widget_query(admin_unit_id, name=None):
    query = CustomWidget.query.filter(CustomWidget.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        query = query.filter(CustomWidget.name.ilike(like_name))

    return query.order_by(func.lower(CustomWidget.name))


def get_place_query(admin_unit_id, name=None):
    query = EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        query = query.filter(EventPlace.name.ilike(like_name))

    return query.order_by(func.lower(EventPlace.name))


def get_event_list_query(admin_unit_id, name=None, event_id=None):
    query = EventList.query.filter(EventList.admin_unit_id == admin_unit_id)

    if name:
        like_name = "%" + name + "%"
        query = query.filter(EventList.name.ilike(like_name))

    return query.order_by(func.lower(EventList.name))


def get_event_list_status_query(admin_unit_id, event_id, name=None):
    event_count = (
        db.session.query(func.count(EventEventLists.id))
        .filter(
            EventEventLists.event_id == event_id,
            EventEventLists.list_id == EventList.id,
        )
        .label("event_count")
    )

    query = db.session.query(EventList, event_count).filter(
        EventList.admin_unit_id == admin_unit_id
    )

    if name:
        like_name = "%" + name + "%"
        query = query.filter(EventList.name.ilike(like_name))

    return query.group_by(EventList.id).order_by(func.lower(EventList.name))


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


def upsert_admin_unit_relation(source_admin_unit_id: int, target_admin_unit_id: int):
    result = get_admin_unit_relation(source_admin_unit_id, target_admin_unit_id)

    if result is None:
        result = insert_admin_unit_relation(source_admin_unit_id, target_admin_unit_id)

    return result


def get_admin_unit_relations_for_reference_requests(
    target_admin_unit_id: int, limit: int
):
    return (
        AdminUnitRelation.query.join(
            AdminUnit,
            AdminUnitRelation.source_admin_unit_id == AdminUnit.id,
        )
        .options(
            joinedload(AdminUnitRelation.source_admin_unit).load_only(
                AdminUnit.id, AdminUnit.name
            ),
        )
        .filter(
            and_(
                AdminUnitRelation.target_admin_unit_id == target_admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
        )
        .order_by(
            AdminUnitRelation.auto_verify_event_reference_requests.desc(),
            AdminUnitRelation.verify.desc(),
            AdminUnitRelation.invited.desc(),
            AdminUnitRelation.created_at.desc(),
        )
        .limit(limit)
        .all()
    )


def get_admin_units_for_reference_requests(admin_unit_id: int, limit: int):
    return (
        AdminUnit.query.options(
            load_only(AdminUnit.id, AdminUnit.name),
        )
        .filter(
            and_(
                AdminUnit.id != admin_unit_id,
                AdminUnit.incoming_reference_requests_allowed,
            )
        )
        .limit(limit)
        .all()
    )


def get_admin_unit_invitation_query(admin_unit):
    return AdminUnitInvitation.query.filter(
        AdminUnitInvitation.admin_unit_id == admin_unit.id
    )


def get_admin_unit_organization_invitations_query(email):
    return AdminUnitInvitation.query.filter(
        func.lower(AdminUnitInvitation.email) == func.lower(email)
    )


def get_admin_unit_organization_invitations(email):
    return get_admin_unit_organization_invitations_query(email).all()


def create_ical_events_for_admin_unit(
    admin_unit: AdminUnit,
) -> list:  # list[icalendar.Event]
    from dateutil.relativedelta import relativedelta

    from project.dateutils import get_today
    from project.services.event import create_ical_events_for_search
    from project.services.event_search import EventSearchParams

    params = EventSearchParams()
    params.date_from = get_today() - relativedelta(months=1)
    params.admin_unit_id = admin_unit.id
    params.can_read_private_events = False

    return create_ical_events_for_search(params)


def get_admin_units_with_due_delete_request():
    due = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    return AdminUnit.query.filter(AdminUnit.deletion_requested_at < due).all()


def delete_admin_unit(admin_unit: AdminUnit):
    db.session.delete(admin_unit)
    db.session.commit()
