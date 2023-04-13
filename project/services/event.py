import os
from datetime import datetime

import icalendar
from dateutil.relativedelta import relativedelta
from flask import url_for
from flask_babelex import format_date, format_time, gettext
from icalendar.prop import vDDDLists
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import aliased, contains_eager, defaultload, joinedload, lazyload
from sqlalchemy.sql import extract

from project import app, db
from project.dateutils import (
    berlin_tz,
    date_add_time,
    date_parts_are_equal,
    dates_from_recurrence_rule,
    get_today,
    round_to_next_day,
)
from project.jinja_filters import url_for_image
from project.models import (
    AdminUnit,
    Event,
    EventAttendanceMode,
    EventCategory,
    EventDate,
    EventDateDefinition,
    EventList,
    EventOrganizer,
    EventPlace,
    EventReference,
    EventStatus,
    Image,
    Location,
    PublicStatus,
    UserFavoriteEvents,
    sanitize_allday_instance,
)
from project.services.event_search import EventSearchParams
from project.services.reference import upsert_event_reference
from project.utils import get_pending_changes, get_place_str
from project.views.utils import truncate


def get_event_category(category_name):
    return EventCategory.query.filter_by(name=category_name).first()


def upsert_event_category(category_name):
    result = get_event_category(category_name)
    if result is None:
        result = EventCategory(name=category_name)
        db.session.add(result)

    return result


def fill_event_filter(event_filter, params):
    if params.keyword:
        tq = func.websearch_to_tsquery("german", params.keyword)
        event_filter = and_(
            event_filter,
            Event.__ts_vector__.op("@@")(tq),
        )

    if params.category_id:
        if type(params.category_id) is list:
            category_ids = params.category_id
        else:
            category_ids = [params.category_id]
        event_filter = and_(
            event_filter, Event.categories.any(EventCategory.id.in_(category_ids))
        )

    if params.status:
        if type(params.status) is list:
            stati = params.status
        else:  # pragma: no cover
            stati = [params.status]
        event_filter = and_(event_filter, Event.status.in_(stati))

    if params.event_list_id:
        if type(params.event_list_id) is list:
            event_list_ids = params.event_list_id
        else:
            event_list_ids = [params.event_list_id]
        event_filter = and_(
            event_filter, Event.event_lists.any(EventList.id.in_(event_list_ids))
        )

    if params.organizer_id:
        event_filter = and_(event_filter, Event.organizer_id == params.organizer_id)

    if params.event_place_id:
        event_filter = and_(event_filter, Event.event_place_id == params.event_place_id)

    if params.latitude and params.longitude and params.distance:
        point = "POINT({} {})".format(params.longitude, params.latitude)
        event_filter = and_(
            event_filter,
            func.ST_DistanceSphere(Location.coordinate, point) <= params.distance,
        )

    if params.postal_code:
        if type(params.postal_code) is list:
            postalCodes = params.postal_code
        else:
            postalCodes = [params.postal_code]

        postalCodeFilters = None
        for postalCode in postalCodes:
            postalCodeFilter = Location.postalCode.ilike(postalCode + "%")
            if postalCodeFilters is not None:
                postalCodeFilters = or_(postalCodeFilters, postalCodeFilter)
            else:
                postalCodeFilters = postalCodeFilter

        if postalCodeFilters is not None:
            event_filter = and_(event_filter, postalCodeFilters)

    if params.favored_by_user_id:
        user_favorite_exists = UserFavoriteEvents.query.filter(
            UserFavoriteEvents.event_id == Event.id,
            UserFavoriteEvents.user_id == params.favored_by_user_id,
        ).exists()
        event_filter = and_(
            event_filter,
            user_favorite_exists,
        )

    return event_filter


def get_event_dates_query(params):
    event_filter = 1 == 1
    date_filter = EventDate.start >= datetime.min

    event_filter = fill_event_filter(event_filter, params)

    admin_unit_reference = None
    if params.admin_unit_id:
        admin_unit_refs_subquery = EventReference.query.filter(
            EventReference.admin_unit_id == params.admin_unit_id
        ).subquery()
        admin_unit_reference = aliased(EventReference, admin_unit_refs_subquery)

        event_filter = and_(
            event_filter,
            or_(
                Event.admin_unit_id == params.admin_unit_id,
                admin_unit_reference.id.isnot(None),
            ),
        )

        if not params.can_read_private_events:
            event_filter = and_(
                event_filter,
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )
    else:
        event_filter = and_(
            event_filter,
            Event.public_status == PublicStatus.published,
            AdminUnit.is_verified,
        )

    if params.date_from:
        date_filter = EventDate.start >= params.date_from

    if params.date_to:
        date_filter = and_(date_filter, EventDate.start < params.date_to)

    # PostgreSQL specific https://stackoverflow.com/a/25597632
    if params.weekday and type(params.weekday) is list:
        weekdays = params.weekday
        date_filter = and_(date_filter, extract("dow", EventDate.start).in_(weekdays))

    result = (
        EventDate.query.join(EventDate.event)
        .join(Event.admin_unit)
        .join(Event.event_place, isouter=True)
        .join(EventPlace.location, isouter=True)
    )

    if admin_unit_reference:
        result = result.join(
            admin_unit_reference,
            Event.id == admin_unit_reference.event_id,
            isouter=True,
        )

    result = (
        result.options(
            contains_eager(EventDate.event)
            .contains_eager(Event.event_place)
            .contains_eager(EventPlace.location),
            joinedload(EventDate.event)
            .joinedload(Event.categories)
            .load_only(EventCategory.id, EventCategory.name),
            joinedload(EventDate.event)
            .joinedload(Event.organizer)
            .load_only(EventOrganizer.id, EventOrganizer.name),
            joinedload(EventDate.event).joinedload(Event.photo).load_only(Image.id),
            joinedload(EventDate.event)
            .joinedload(Event.admin_unit)
            .load_only(AdminUnit.id, AdminUnit.name),
        )
        .filter(date_filter)
        .filter(event_filter)
    )

    if params.sort == "-rating":
        if admin_unit_reference:
            result = result.order_by(
                case(
                    [
                        (
                            admin_unit_reference.rating.isnot(None),
                            admin_unit_reference.rating,
                        ),
                    ],
                    else_=Event.rating,
                ).desc()
            )
        else:
            result = result.order_by(Event.rating.desc())

    result = result.order_by(EventDate.start)
    return result


def get_event_date_with_details_or_404(event_id):
    return (
        EventDate.query.join(EventDate.event)
        .join(Event.event_place, isouter=True)
        .join(EventPlace.location, isouter=True)
        .options(
            contains_eager(EventDate.event)
            .contains_eager(Event.event_place)
            .contains_eager(EventPlace.location),
            joinedload(EventDate.event).undefer_group("trackable"),
            # Place
            defaultload(EventDate.event)
            .defaultload(Event.event_place)
            .joinedload(EventPlace.photo),
            # Category
            joinedload(EventDate.event)
            .joinedload(Event.categories)
            .load_only(EventCategory.id, EventCategory.name),
            # Organizer
            joinedload(EventDate.event)
            .joinedload(Event.organizer)
            .undefer_group("detail")
            .undefer("logo_id")
            .joinedload(EventOrganizer.logo),
            # Photo
            joinedload(EventDate.event).joinedload(Event.photo),
            # Admin unit
            joinedload(EventDate.event)
            .joinedload(Event.admin_unit)
            .undefer("logo_id")
            .undefer_group("detail")
            .undefer_group("widget")
            .joinedload(AdminUnit.location),
            # Admin unit logo
            defaultload(EventDate.event)
            .defaultload(Event.admin_unit)
            .joinedload(AdminUnit.logo),
        )
        .filter(EventDate.id == event_id)
        .first_or_404()
    )


def get_event_with_details_or_404(event_id):
    return (
        Event.query.join(EventPlace, isouter=True)
        .join(Location, isouter=True)
        .options(
            contains_eager(Event.event_place).contains_eager(EventPlace.location),
            defaultload(Event).undefer_group("trackable"),
            # Place
            joinedload(Event.event_place).joinedload(EventPlace.photo),
            # Category
            joinedload(Event.categories).load_only(
                EventCategory.id, EventCategory.name
            ),
            # Organizer
            joinedload(Event.organizer)
            .undefer_group("detail")
            .undefer("logo_id")
            .joinedload(EventOrganizer.logo),
            # Photo
            joinedload(Event.photo),
            # Admin unit with location
            joinedload(Event.admin_unit)
            .undefer("logo_id")
            .undefer_group("detail")
            .undefer_group("widget")
            .joinedload(AdminUnit.location),
            # Admin unit logo
            defaultload(Event.admin_unit).joinedload(AdminUnit.logo),
        )
        .filter(Event.id == event_id)
        .first_or_404()
    )


def get_events_query(params):
    event_filter = 1 == 1
    date_filter = EventDate.start >= datetime.min

    event_filter = fill_event_filter(event_filter, params)

    if params.admin_unit_id:
        event_filter = and_(event_filter, Event.admin_unit_id == params.admin_unit_id)

        if not params.can_read_private_events:
            event_filter = and_(
                event_filter,
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )
    else:
        event_filter = and_(
            event_filter,
            Event.public_status == PublicStatus.published,
            AdminUnit.is_verified,
        )

    if params.date_from:
        date_filter = EventDate.start >= params.date_from

    if params.date_to:
        date_filter = and_(date_filter, EventDate.start < params.date_to)

    event_filter = and_(event_filter, Event.dates.any(date_filter))
    return (
        Event.query.join(Event.admin_unit)
        .join(Event.event_place, isouter=True)
        .join(EventPlace.location, isouter=True)
        .options(
            contains_eager(Event.event_place).contains_eager(EventPlace.location),
            joinedload(Event.categories),
            joinedload(Event.organizer),
            joinedload(Event.photo),
            joinedload(Event.admin_unit),
        )
        .filter(event_filter)
        .order_by(Event.min_start)
    )


def get_recurring_events():
    return Event.query.filter(Event.is_recurring).all()


def update_event_dates_with_recurrence_rule(event):
    dates_to_add = list()
    dates_to_remove = list(event.dates)

    for date_definition in event.date_definitions:
        sanitize_allday_instance(date_definition)
        start = date_definition.start
        end = date_definition.end

        if end:
            time_difference = relativedelta(end, start)

        if date_definition.recurrence_rule:
            rr_dates = dates_from_recurrence_rule(
                start, date_definition.recurrence_rule
            )
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
                    if date.start == rr_date_start
                    and date.end == rr_date_end
                    and date.allday == date_definition.allday
                ),
                None,
            )
            if existing_date:
                if existing_date in dates_to_remove:
                    dates_to_remove.remove(existing_date)
            else:
                new_date = EventDate(
                    event_id=event.id,
                    start=rr_date_start,
                    end=rr_date_end,
                    allday=date_definition.allday,
                )
                dates_to_add.append(new_date)

    event.dates = [date for date in event.dates if date not in dates_to_remove]
    event.dates.extend(dates_to_add)


def insert_event(event):
    if not event.status:
        event.status = EventStatus.scheduled

    if not event.public_status:
        event.public_status = PublicStatus.published

    update_event_dates_with_recurrence_rule(event)
    db.session.add(event)


def update_event(event):
    with db.session.no_autoflush:
        update_event_dates_with_recurrence_rule(event)


def get_upcoming_event_dates(event_id):
    today = get_today()
    return (
        EventDate.query.options(lazyload(EventDate.event))
        .filter(and_(EventDate.event_id == event_id, EventDate.start >= today))
        .order_by(EventDate.start)
        .all()
    )


def get_significant_event_changes(event) -> dict:
    keys = [
        "name",
        "start",
        "recurrence_rule",
        "status",
        "attendance_mode",
        "booked_up",
        "event_place_id",
        "organizer_id",
    ]
    return get_pending_changes(event, include_collections=False, include_keys=keys)


def get_meta_data(event: Event, event_date: EventDate = None) -> dict:
    meta = dict()
    meta["title"] = event.name

    if (
        event.attendance_mode
        and event.attendance_mode != EventAttendanceMode.online
        and event.event_place
    ):
        meta["title"] = f"{meta['title']} @ {event.event_place.name}"

        if event.event_place.location and event.event_place.location.city:
            meta["title"] = f"{meta['title']}, {event.event_place.location.city}"

    if event_date:
        date_str = format_date(event_date.start, "full")
        time_str = format_time(event_date.start, "short")
        meta["description"] = f"{date_str} {time_str}"

    if event.description:
        desc_short = truncate(event.description, 300)

        if "description" in meta:
            meta["description"] = f"{meta['description']}: {desc_short}"
        else:
            meta["description"] = desc_short

    if event.photo_id:
        meta["image"] = url_for_image(event.photo, _external=True)

    return meta


def populate_ical_event_with_event(
    ical_event: icalendar.Event, model_event: Event, url: str
):
    ical_event.add("url", url)
    ical_event.add("summary", model_event.name)

    if model_event.created_at:
        ical_event.add("dtstamp", model_event.created_at)

    if model_event.updated_at:
        ical_event.add("last-modified", model_event.updated_at)

    if model_event.status and model_event.status == EventStatus.cancelled:
        ical_event.add("status", "CANCELLED")

    desc_items = list()
    desc_items.append(url)

    if model_event.organizer:
        desc_items.append(f"{gettext('Organizer')}: {model_event.organizer.name}")

    if model_event.admin_unit:
        desc_items.append(f"{gettext('Organization')}: {model_event.admin_unit.name}")

    if model_event.description:
        desc_short = truncate(model_event.description, 300)
        desc_items.append(f"{os.linesep}{desc_short}")

    ical_event.add("description", os.linesep.join(desc_items))

    if (
        model_event.attendance_mode
        and model_event.attendance_mode != EventAttendanceMode.online
        and model_event.event_place
    ):
        place = model_event.event_place
        place_str = get_place_str(place)
        ical_event.add("location", place_str)

        location = place.location
        if location and location.coordinate:
            ical_event.add("geo", (location.latitude, location.longitude))
            ical_event.add(
                "X-APPLE-STRUCTURED-LOCATION",
                f"geo:{location.latitude},{location.longitude}",
                parameters={
                    "VALUE": "URI",
                    "X-ADDRESS": place_str,  # must be same as "location"
                    "X-APPLE-RADIUS": "100",
                    "X-TITLE": place_str,  # must be same as "location"
                },
            )


def populate_ical_event_with_datish(
    ical_event: icalendar.Event, datish, recurrence_rule: str = None
):
    # datish: EventDate|EventDateDefinition
    start = datish.start.astimezone(berlin_tz)

    if datish.allday:
        ical_event.add("dtstart", icalendar.vDate(start))
    else:
        ical_event.add("dtstart", start)

    if recurrence_rule:
        recc_lines = recurrence_rule.splitlines()

        for recc_line in recc_lines:
            recc_line_parts = recc_line.split(":", 1)

            if len(recc_line_parts) != 2:  # pragma: no cover
                continue

            recc_key, recc_value = recc_line_parts
            recc_key_lower = recc_key.lower()

            if recc_key_lower == "rrule":
                ical_event.add("rrule", icalendar.vRecur.from_ical(recc_value))
            elif recc_key_lower == "exdate":
                ical_event.add("exdate", vDDDLists.from_ical(recc_value))
            elif recc_key_lower == "rdate":
                ical_event.add("rdate", vDDDLists.from_ical(recc_value))

    if datish.end and datish.end > datish.start:
        end = datish.end.astimezone(berlin_tz)

        if datish.allday:
            if not date_parts_are_equal(start, end):
                next_day = round_to_next_day(end)
                ical_event.add("dtend", icalendar.vDate(next_day))
        else:
            ical_event.add("dtend", end)


def create_ical_event_for_date(event_date: EventDate) -> icalendar.Event:
    url = url_for("event_date", id=event_date.id, _external=True)

    ical_event = icalendar.Event()
    populate_ical_event_with_event(ical_event, event_date.event, url)
    populate_ical_event_with_datish(ical_event, event_date)
    ical_event.add("uid", url)

    return ical_event


def create_ical_event_for_date_definition(
    date_definition: EventDateDefinition,
) -> icalendar.Event:
    url = url_for("event", event_id=date_definition.event.id, _external=True)

    ical_event = icalendar.Event()
    populate_ical_event_with_event(ical_event, date_definition.event, url)
    populate_ical_event_with_datish(
        ical_event, date_definition, date_definition.recurrence_rule
    )

    ical_event.add("uid", f"{url}#{date_definition.id}")

    return ical_event


def create_ical_events_for_event(event: Event) -> list:  # list[icalendar.Event]
    result = list()

    for date_definition in event.date_definitions:
        try:
            ical_event = create_ical_event_for_date_definition(date_definition)
            result.append(ical_event)
        except Exception as e:  # pragma: no cover
            app.logger.exception(e)

    return result


def create_ical_events_for_search(
    params: EventSearchParams,
) -> list:  # list[icalendar.Event]
    result = list()
    events = get_events_query(params).all()

    for event in events:
        ical_events = create_ical_events_for_event(event)
        result.extend(ical_events)

    return result


def update_recurring_dates():
    # Setting the timezone is neccessary for cli command
    db.session.execute("SET timezone TO :val;", {"val": berlin_tz.zone})

    events = get_recurring_events()

    for event in events:
        update_event_dates_with_recurrence_rule(event)
        db.session.commit()

    app.logger.info(f"{len(events)} event(s) were updated.")


def create_bulk_event_references(admin_unit_id: int, postalCodes: list):
    params = EventSearchParams()
    params.set_default_date_range()
    params.postal_code = postalCodes

    query = get_events_query(params)
    query = query.filter(Event.admin_unit_id != admin_unit_id)

    count = 0
    events = query.all()
    for event in events:
        if upsert_event_reference(event.id, admin_unit_id):
            count = count + 1

    db.session.commit()
    app.logger.info(f"{count} reference(s) created.")
