from sqlalchemy import and_

from project import db
from project.models import EventOrganizer, Location


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


def create_ical_events_for_organizer(
    organizer: EventOrganizer,
) -> list:  # list[icalendar.Event]
    from dateutil.relativedelta import relativedelta

    from project.dateutils import get_today
    from project.services.event import create_ical_events_for_search
    from project.services.search_params import EventSearchParams

    params = EventSearchParams()
    params.date_from = get_today() - relativedelta(months=1)
    params.organizer_id = organizer.id
    params.can_read_private_events = False

    return create_ical_events_for_search(params)
