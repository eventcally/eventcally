import datetime
import decimal
from json import JSONEncoder
from flask import url_for

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)

def get_sd_for_org(organization):
    result = {}
    result["@type"] = "Organization"
    result["identifier"] = str(organization.id)
    result["url"] = url_for('organization', organization_id=organization.id)
    result["name"] = organization.name

    if organization.logo_id:
        result["logo"] = url_for('image', id=organization.logo_id)

    if organization.email:
        result["email"] = organization.email

    if organization.phone:
        result["phone"] = organization.phone

    return result

def get_sd_for_admin_unit(admin_unit):
    result = {}
    result["@type"] = "GovernmentOrganization"
    result["identifier"] = str(admin_unit.id)
    result["url"] = url_for('admin_unit', admin_unit_id=admin_unit.id)
    result["name"] = admin_unit.name
    return result

def get_sd_for_ooa(ooa):
    if ooa.organization:
        return get_sd_for_org(ooa.organization)

    return get_sd_for_admin_unit(ooa.admin_unit)

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

def get_sd_for_place(place):
    result = {}
    result["@type"] = "Place"
    result["identifier"] = str(place.id)
    result["url"] = url_for('place', place_id=place.id)
    result["name"] = place.name

    if place.location:
        result["address"] = get_sd_for_location(place.location)

        if place.location.latitude != 0:
            result["geo"] = get_sd_for_geo(place.location)

    if place.photo_id:
        result["photo"] = url_for('image', id=place.photo_id)

    return result

def get_sd_for_event_date(event_date):
    event = event_date.event

    result = {}
    result["@context"] = "https://schema.org"
    result["@type"] = "Event"
    result["identifier"] = str(event_date.id)
    result["url"] = url_for('event_date', id=event_date.id)
    result["name"] = event.name
    result["description"] = event.description
    result["startDate"] = event_date.start
    result["location"] = get_sd_for_place(event.place)
    result["organizer"] = get_sd_for_ooa(event.host)

    if event.photo_id:
        result["image"] = url_for('image', id=event.photo_id)

    return result
