"""iCal builders over the event read models."""

import logging
import re

import icalendar
from flask import url_for
from flask_babel import gettext
from icalendar.prop import vDDDLists

from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_status import EventStatus
from project.domain.types.text import normalize_newlines
from project.presentation.web.views.utils import truncate
from project.shared.dateutils import berlin_tz, date_parts_are_equal, round_to_next_day
from project.shared.utils import get_place_str

logger = logging.getLogger(__name__)

# RFC 5545 TEXT allows no CONTROL characters except HTAB; LF is escaped by icalendar.
_FORBIDDEN_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def ical_text(value):
    """Free text made safe for an iCal TEXT value: CRLF and a lone CR become LF
    (icalendar escapes LF as `\\n`), other control characters are dropped."""
    if not value:
        return value
    return _FORBIDDEN_CONTROL_CHARS.sub("", normalize_newlines(value))


def ical_single_line(value):
    """`ical_text` on one line, for values that are also parameter values
    (parameters cannot escape line breaks); double quotes become single quotes
    because DQUOTE is illegal in a parameter value."""
    if not value:
        return value
    lines = (line.strip() for line in ical_text(value).split("\n"))
    return ", ".join(line for line in lines if line).replace('"', "'")


def populate_ical_event_with_event(ical_event: icalendar.Event, event, url: str):
    ical_event.add("url", url)
    ical_event.add("summary", ical_text(event.name))

    if event.created_at:
        ical_event.add("dtstamp", event.created_at)

    if event.last_modified_at:
        ical_event.add("last-modified", event.last_modified_at)

    if event.status and event.status == EventStatus.cancelled:
        ical_event.add("status", "CANCELLED")

    desc_items = list()
    desc_items.append(url)

    if event.organizer:
        organizer_name = ical_text(event.organizer.name)
        desc_items.append(f"{gettext('Organizer')}: {organizer_name}")
        ical_event.add("x-eventcally-organizer", organizer_name)

    if event.admin_unit:
        admin_unit_name = ical_text(event.admin_unit.name)
        desc_items.append(f"{gettext('Organization')}: {admin_unit_name}")
        ical_event.add("x-eventcally-organization", admin_unit_name)

    if event.description:
        desc_short = truncate(ical_text(event.description), 300)
        desc_items.append(f"\n{desc_short}")

    ical_event.add("description", "\n".join(desc_items))

    if (
        event.attendance_mode
        and event.attendance_mode != EventAttendanceMode.online
        and event.event_place
    ):
        place = event.event_place
        place_str = ical_single_line(get_place_str(place))
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
    # datish: an event date or an event date definition
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


def create_ical_event_for_date(event_date) -> icalendar.Event:
    """`event_date.event` is the event read model."""
    url = url_for("main.event_date", id=event_date.id, _external=True)

    ical_event = icalendar.Event()
    populate_ical_event_with_event(ical_event, event_date.event, url)
    populate_ical_event_with_datish(ical_event, event_date)
    ical_event.add("uid", url)

    return ical_event


def create_ical_event_for_date_definition(event, date_definition) -> icalendar.Event:
    url = url_for("main.event", event_id=event.id, _external=True)

    ical_event = icalendar.Event()
    populate_ical_event_with_event(ical_event, event, url)
    populate_ical_event_with_datish(
        ical_event, date_definition, date_definition.recurrence_rule
    )

    ical_event.add("uid", f"{url}#{date_definition.id}")

    return ical_event


def create_ical_events_for_event(event) -> list:  # list[icalendar.Event]
    result = list()

    for date_definition in event.date_definitions:
        try:
            ical_event = create_ical_event_for_date_definition(event, date_definition)
            result.append(ical_event)
        except Exception:  # pragma: no cover
            logger.exception(
                "Could not create the iCal event",
                extra={"event_id": event.id, "date_definition_id": date_definition.id},
            )

    return result


def create_ical_events_for_events(events) -> list:  # list[icalendar.Event]
    result = list()

    for event in events:
        result.extend(create_ical_events_for_event(event))

    return result
