from project import db
from project.models import (
    EventCategory,
    Event,
    EventDate,
    EventReference,
    EventPlace,
    Location,
)
from project.dateutils import (
    dates_from_recurrence_rule,
    today,
    date_add_time,
)
from sqlalchemy import and_, or_, func
from sqlalchemy.sql import extract
from dateutil.relativedelta import relativedelta


def upsert_event_category(category_name):
    result = EventCategory.query.filter_by(name=category_name).first()
    if result is None:
        result = EventCategory(name=category_name)
        db.session.add(result)

    return result


def fill_event_filter(event_filter, params):
    if params.keyword:
        like_keyword = "%" + params.keyword + "%"
        event_filter = and_(
            event_filter,
            or_(
                Event.name.ilike(like_keyword),
                Event.description.ilike(like_keyword),
                Event.tags.ilike(like_keyword),
            ),
        )

    if params.category_id:
        if type(params.category_id) is list:
            category_ids = params.category_id
        else:
            category_ids = [params.category_id]
        event_filter = and_(
            event_filter, Event.categories.any(EventCategory.id.in_(category_ids))
        )

    if params.organizer_id:
        event_filter = and_(event_filter, Event.organizer_id == params.organizer_id)

    if params.latitude and params.longitude and params.distance:
        point = "POINT({} {})".format(params.longitude, params.latitude)
        event_filter = and_(
            event_filter,
            func.ST_DistanceSphere(Location.coordinate, point) <= params.distance,
        )

    return event_filter


def get_event_dates_query(params):
    event_filter = 1 == 1
    date_filter = EventDate.start >= today

    event_filter = fill_event_filter(event_filter, params)

    if params.admin_unit_id:
        event_filter = and_(
            event_filter,
            or_(
                Event.admin_unit_id == params.admin_unit_id,
                Event.references.any(
                    EventReference.admin_unit_id == params.admin_unit_id
                ),
            ),
        )

    if params.date_from:
        date_filter = EventDate.start >= params.date_from

    if params.date_to:
        date_filter = and_(date_filter, EventDate.start < params.date_to)

    # PostgreSQL specific https://stackoverflow.com/a/25597632
    if params.weekday and type(params.weekday) is list:
        weekdays = params.weekday
        date_filter = and_(date_filter, extract("dow", EventDate.start).in_(weekdays))

    return (
        EventDate.query.join(Event)
        .join(EventPlace, isouter=True)
        .join(Location, isouter=True)
        .filter(date_filter)
        .filter(event_filter)
        .order_by(EventDate.start)
    )


def get_events_query(params):
    event_filter = 1 == 1
    date_filter = EventDate.start >= today

    event_filter = fill_event_filter(event_filter, params)

    if params.admin_unit_id:
        event_filter = and_(event_filter, Event.admin_unit_id == params.admin_unit_id)

    if params.date_from:
        date_filter = EventDate.start >= params.date_from

    if params.date_to:
        date_filter = and_(date_filter, EventDate.start < params.date_to)

    event_filter = and_(event_filter, Event.dates.any(date_filter))
    return (
        Event.query.join(EventPlace, isouter=True)
        .join(Location, isouter=True)
        .filter(event_filter)
        .order_by(Event.start)
    )


def update_event_dates_with_recurrence_rule(event):
    start = event.start
    end = event.end

    if end:
        time_difference = relativedelta(end, start)

    dates_to_add = list()
    dates_to_remove = list(event.dates)

    if event.recurrence_rule:
        rr_dates = dates_from_recurrence_rule(start, event.recurrence_rule)
    else:
        rr_dates = [start]

    for rr_date in rr_dates:
        rr_date_start = date_add_time(
            rr_date, start.hour, start.minute, start.second, rr_date.tzinfo
        )

        if end:
            rr_date_end = rr_date_start + time_difference
        else:
            rr_date_end = None

        existing_date = next(
            (
                date
                for date in event.dates
                if date.start == rr_date_start and date.end == rr_date_end
            ),
            None,
        )
        if existing_date:
            dates_to_remove.remove(existing_date)
        else:
            new_date = EventDate(
                event_id=event.id, start=rr_date_start, end=rr_date_end
            )
            dates_to_add.append(new_date)

    event.dates = [date for date in event.dates if date not in dates_to_remove]
    event.dates.extend(dates_to_add)


def insert_event(event):
    update_event_dates_with_recurrence_rule(event)
    db.session.add(event)


def update_event(event):
    update_event_dates_with_recurrence_rule(event)
