import datetime

from flask import url_for
from flask.json.provider import DefaultJSONProvider

from project.dateutils import berlin_tz
from project.jinja_filters import url_for_image
from project.models import EventAttendanceMode, EventStatus


class CustomJsonProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, datetime.datetime):
            return (obj.astimezone(berlin_tz)).isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()

        return super(CustomJsonProvider, CustomJsonProvider).default(
            obj
        )  # pragma: no cover


def get_sd_for_admin_unit(admin_unit):
    result = {}
    result["@type"] = "Organization"
    result["identifier"] = str(admin_unit.id)
    result["name"] = admin_unit.name

    if admin_unit.url:
        result["url"] = admin_unit.url

    return result


def get_sd_for_organizer(organizer):
    result = {}
    result["@type"] = "Organization"
    result["name"] = organizer.name

    if organizer.email:
        result["email"] = organizer.email

    if organizer.phone:
        result["phone"] = organizer.phone

    if organizer.fax:
        result["faxNumber"] = organizer.fax

    if organizer.url:
        result["url"] = organizer.url

    return result


def get_sd_for_location(location):
    result = {}
    result["@type"] = "PostalAddress"
    result["addressCountry"] = "DE"

    if location.street:
        result["streetAddress"] = location.street
    if location.postalCode:
        result["postalCode"] = location.postalCode
    if location.city:
        result["addressLocality"] = location.city

    return result


def get_sd_for_geo(location):
    result = {}
    result["@type"] = "GeoCoordinates"
    result["latitude"] = location.latitude
    result["longitude"] = location.longitude
    return result


def get_sd_for_place(place, use_ref=True):
    result = {}
    result["@type"] = "Place"
    result["name"] = place.name

    if place.location:
        result["address"] = get_sd_for_location(place.location)

        if place.location.coordinate:
            result["geo"] = get_sd_for_geo(place.location)

    if place.photo_id:
        result["photo"] = url_for_image(place.photo)

    if place.url:
        result["url"] = place.url

    return result


def get_date_from_datetime(value: datetime.datetime) -> datetime.date:
    return value.astimezone(berlin_tz).date()


def get_sd_for_event_date(event_date):
    event = event_date.event

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Event"
    result["identifier"] = str(event_date.id)
    result["name"] = event.name
    result["description"] = event.description
    result["startDate"] = event_date.start

    if event_date.end:
        result["endDate"] = event_date.end

    if event.previous_start_date:
        result["previousStartDate"] = event.previous_start_date

    if event_date.allday:
        result["startDate"] = get_date_from_datetime(result["startDate"])

        if event_date.end:
            result["endDate"] = get_date_from_datetime(result["endDate"])

    url_list = list()
    url_list.append(url_for("event_date", id=event_date.id))

    if event.external_link:
        url_list.append(event.external_link)

    if event.ticket_link:
        url_list.append(event.ticket_link)

    result["url"] = url_list

    result["location"] = get_sd_for_place(event.event_place)

    organizer_list = list()

    if event.organizer:
        organizer_list.append(get_sd_for_organizer(event.organizer))

    for co_organizer in event.co_organizers:
        organizer_list.append(get_sd_for_organizer(co_organizer))

    if event.admin_unit:
        organizer_list.append(get_sd_for_admin_unit(event.admin_unit))
    result["organizer"] = organizer_list

    if event.accessible_for_free:
        result["isAccessibleForFree"] = event.accessible_for_free

    if event.age_from and event.age_to:
        result["typicalAgeRange"] = "%d-%d" % (event.age_from, event.age_to)
    elif event.age_from:
        result["typicalAgeRange"] = "%d-" % event.age_from
    elif event.age_to:
        result["typicalAgeRange"] = "-%d" % event.age_to

    if event.attendance_mode:
        if event.attendance_mode == EventAttendanceMode.offline:
            result["eventAttendanceMode"] = "OfflineEventAttendanceMode"
        elif event.attendance_mode == EventAttendanceMode.online:
            result["eventAttendanceMode"] = "OnlineEventAttendanceMode"
        elif event.attendance_mode == EventAttendanceMode.mixed:
            result["eventAttendanceMode"] = "MixedEventAttendanceMode"

    if event.status:
        if event.status == EventStatus.scheduled:
            result["eventStatus"] = "EventScheduled"
        elif event.status == EventStatus.cancelled:
            result["eventStatus"] = "EventCancelled"
        elif event.status == EventStatus.movedOnline:
            result["eventStatus"] = "EventMovedOnline"
        elif event.status == EventStatus.postponed:
            result["eventStatus"] = "EventPostponed"
        elif event.status == EventStatus.rescheduled:
            result["eventStatus"] = "EventRescheduled"

    if event.photo_id:
        result["image"] = url_for_image(event.photo)

    return result
