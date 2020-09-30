from app import app, db, get_admin_unit, update_event_dates_with_recurrence_rule, upsert_event_category
from pprint import pprint
import datetime
from dateutil import parser, tz
import pytz
from urllib.request import urlopen, URLError
from bs4 import BeautifulSoup
import requests
from os import path
import json
import re
import unicodedata
import decimal
from models import EventReviewStatus, EventTargetGroupOrigin, Location, Event, EventStatus, EventCategory, EventPlace, EventOrganizer, AdminUnit
from sqlalchemy import and_, or_, not_

berlin_tz = pytz.timezone('Europe/Berlin')

def scrape(debug):
    url = 'https://goslar.feripro.de/programm/42/anmeldung/veranstaltungen'

    if debug:
        filename = "tmp/fp.html"

        if not path.exists(filename):
            response = urlopen(url)
            with open(filename, "wb") as text_file:
                text_file.write(response.read())

        doc = BeautifulSoup(open(filename), 'html.parser')
    else:
        response = urlopen(url)
        doc = BeautifulSoup(response, 'html.parser')

    js_assigns_regex = r"(\w*)\s*:\s*JSON\.parse\('(.*)'\)"
    js_assigns = dict()
    javascripts = doc.find_all('script')
    for javascript in javascripts:
        javascript_contents = javascript.contents[0] if len(javascript.contents) > 0 else ''

        if 'window.fp_initial' in javascript_contents:
            matches = re.findall(js_assigns_regex, javascript_contents, re.MULTILINE)
            for match in matches:
                key = match[0]

                if not key in ['events']:
                    continue

                json_str = match[1]
                decoded_json_str = json_str.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
                value = json.loads(decoded_json_str, strict=False)
                js_assigns[key] = value
            break

    admin_unit = get_admin_unit('Ferienpass Goslar')
    category = upsert_event_category('Other')

    for js_event in js_assigns['events']:
        if not 'event_id' in js_event:
            continue

        event_id = js_event['event_id']
        if not event_id:
            continue

        try:
            external_link = url + '#' + str(event_id)
            event = Event.query.filter(Event.external_link == external_link).first()
            did_create = False

            # Event
            if event is None:

                if js_event['name'] in ['Entfällt', 'Diese Veranstaltung muss leider ausfallen ...']:
                    continue

                event = Event()
                event.admin_unit = admin_unit
                did_create = True

            event.category = category
            event.external_link = external_link
            event.review_status = EventReviewStatus.verified
            event.rating = 5
            event.target_group_origin = EventTargetGroupOrigin.resident
            event.name = js_event['name']
            event.description = js_event['description']
            start = parse_date_time_str(js_event['start'])
            end = parse_date_time_str(js_event['end'])
            update_event_dates_with_recurrence_rule(event, start, end)

            # Organizer
            js_organizer = js_event['organizer']
            organizer_name = js_event['name_public'] if js_event['name_public'] else js_organizer['name']
            organizer_phone = js_event['phone_public'] if js_event['phone_public'] else js_organizer['phone']
            organizer_email = js_event['email_public'] if js_event['email_public'] else js_organizer['email']
            organizer_url = js_organizer['website'] if js_organizer['website'] else js_organizer['facebook']

            organizer = EventOrganizer.query.filter(and_(
                EventOrganizer.admin_unit_id == admin_unit.id,
                EventOrganizer.name == organizer_name)).first()

            if organizer is None:
                organizer = EventOrganizer(
                    admin_unit_id = admin_unit.id,
                    name = organizer_name)

            organizer.phone = organizer_phone
            organizer.email = organizer_email
            organizer.url = organizer_url
            event.organizer = organizer

            # Place
            place_name = ""
            place_description = ""
            place_location = None

            meeting_point = js_event['meeting_point'].replace('\r\n', ', ')
            if len(meeting_point) > 80:
                place_name = meeting_point[:80] + '...'
                place_description = meeting_point
            else:
                place_name = meeting_point

            if 'meeting_point_latitude' in js_event and 'meeting_point_longitude' in js_event:
                meeting_point_latitude = js_event['meeting_point_latitude']
                meeting_point_longitude = js_event['meeting_point_longitude']
                if meeting_point_latitude and meeting_point_longitude:
                    latitude = decimal.Decimal(meeting_point_latitude)
                    longitude = decimal.Decimal(meeting_point_longitude)
                    if latitude != 0 and longitude != 0:
                        place_location = Location()
                        place_location.latitude = latitude
                        place_location.longitude = longitude

            place = EventPlace.query.filter(and_(
                EventPlace.admin_unit_id == admin_unit.id,
                EventPlace.organizer_id == organizer.id,
                EventPlace.name == place_name)).first()

            if place is None:
                place = EventPlace(
                    admin_unit_id = admin_unit.id,
                    organizer_id = organizer.id,
                    name = place_name)

            place.description = place_description
            place.location = place_location
            event.event_place = place

            # Additional data
            event.status = EventStatus.cancelled if js_event['canceled'] else EventStatus.scheduled
            event.kid_friendly = True
            event.accessible_for_free = js_event['price'] == '0.00'

            tag_list = js_event['tags']
            tag_list.append('Ferienpass')
            event.tags = ','.join(tag_list)

            if js_event['min_age']:
                event.age_from = int(js_event['min_age'])

            if js_event['max_age']:
                event.age_to = int(js_event['max_age'])

            print("%s %s %s %s" % (event.dates[0].start, event.name, organizer.id, organizer.name))
            if did_create:
                db.session.add(event)

            db.session.commit()
        except:
            print("Exception")
            pprint(js_event)

def parse_date_time_str(date_time_str):
    if not date_time_str:
        return None

    date_time = datetime.datetime.fromisoformat(date_time_str)
    return berlin_tz.localize(date_time)

if __name__ == '__main__':
    scrape(False)
