from project import db
from project.models import EventOrganizer, EventPlace, Location
from sqlalchemy import and_
from sqlalchemy.sql import func


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


def get_event_places(organizer_id):
    organizer = EventOrganizer.query.get(organizer_id)
    return (
        EventPlace.query.filter(EventPlace.admin_unit_id == organizer.admin_unit_id)
        .order_by(func.lower(EventPlace.name))
        .all()
    )
