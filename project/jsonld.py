import datetime
import decimal
from json import JSONEncoder
from flask import url_for
from project.models import EventAttendanceMode, EventStatus
import pytz

berlin_tz = pytz.timezone('Europe/Berlin')

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return (obj.astimezone(berlin_tz)).isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)

def get_sd_for_admin_unit(admin_unit):
    result = {}
    result["@type"] = "Organization"
    result["identifier"] = str(admin_unit.id)
    result["name"] = admin_unit.name

    if admin_unit.url:
        result["url"] = admin_unit.url

    return result

def get_sd_for_organizer_organization(organizer):
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

def get_sd_for_organizer(organizer):
    return get_sd_for_organizer_organization(organizer)

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

        if place.location.latitude != 0:
            result["geo"] = get_sd_for_geo(place.location)

    if place.photo_id:
        result["photo"] = url_for('image', id=place.photo_id)

    if place.url:
        result["url"] = place.url

    return result

def get_sd_for_event_date(event_date):
    event = event_date.event

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Event"
    result["identifier"] = str(event_date.id)
    result["name"] = event.name
    result["description"] = event.description
    result["startDate"] = event_date.start

    url_list = list()
    url_list.append(url_for('event_date', id=event_date.id))

    if event.external_link:
        url_list.append(event.external_link)

    if event.ticket_link:
        url_list.append(event.ticket_link)

    result["url"] = url_list

    result["location"] = get_sd_for_place(event.event_place)

    organizer_list = list()
    if event.organizer:
        organizer_list.append(get_sd_for_organizer(event.organizer))
    if event.admin_unit:
        organizer_list.append(get_sd_for_admin_unit(event.admin_unit))
    result["organizer"] = organizer_list

    if event_date.end:
        result["endDate"] = event_date.end

    if event.previous_start_date:
        result["previousStartDate"] = event.previous_start_date

    if event.accessible_for_free:
        result["accessible_for_free"] = event.accessible_for_free

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
        result["image"] = url_for('image', id=event.photo_id)

    return result
