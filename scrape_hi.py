from app import app, db
from pprint import pprint
import datetime
from dateutil import parser, tz
import pytz
from urllib import request, parse
from urllib.request import urlopen, URLError
from bs4 import BeautifulSoup
import requests
from os import path
import json
from flask import jsonify
import re
import unicodedata
import decimal
from models import EventReviewStatus, EventTargetGroupOrigin, Location, Event, EventStatus, EventCategory, EventPlace, EventOrganizer, AdminUnit
from sqlalchemy import and_, or_, not_
from dateutils import berlin_tz
from services.admin_unit import get_admin_unit
from services.event import upsert_event_category, update_event_dates_with_recurrence_rule

admin_unit = get_admin_unit('Harzinfo')
category = upsert_event_category('Other')
base_url = "https://www.harzinfo.de"
url = base_url + "/?ndssearch=fullsearch&no_cache=1&L=0"

with open('scrape_hi_req.json') as json_file:
    request_object = json.load(json_file)

with open('scrape_hi_cities.json') as json_file:
    cities = json.load(json_file)

def response_from_url(city):
    body = request_object
    body["searchFilter"]["ndsdestinationdataevent"]["city"] = { str(city['id']): city['short_name'] or city['title'] }
    req =  request.Request(url, data=bytes(json.dumps(body), encoding='utf-8'))
    req.add_header('Content-Type', 'application/json')
    return request.urlopen(req)

def load_json(debug, city):
    if debug:
        filename = "tmp/hi_%d.html" % (city['id'])

        if not path.exists(filename):
            response = response_from_url(city)
            with open(filename, "wb") as text_file:
                text_file.write(response.read())

        with open(filename) as json_file:
            return json.load(json_file)
    else:
        response = response_from_url(city)
        return json.load(response)

def parse_date_time_str(date_time_str):
    if not date_time_str:
        return None

    return datetime.datetime.fromisoformat(date_time_str + ':00')

def scrape(debug, city):

    # Organizer
    organizer_name = city['short_name'] or city['title']
    organizer = EventOrganizer.query.filter(and_(
        EventOrganizer.admin_unit_id == admin_unit.id,
        EventOrganizer.name == organizer_name)).first()

    if organizer is None:
        organizer = EventOrganizer(
            admin_unit_id = admin_unit.id,
            name = organizer_name)
        db.session.add(organizer)
        db.session.commit()

    print(organizer_name)
    response = load_json(debug, city)
    result = response["result"]
    event_ids = list()

    for item in result:
        try:
            uid = str(item["uid"])
            external_link = base_url + item["link"] + '#' + uid
            event = Event.query.filter(and_(Event.organizer_id == organizer.id, Event.external_link == external_link)).first()
            did_create = False

            if event is None:
                event = Event()
                event.admin_unit = admin_unit
                event.organizer = organizer
                did_create = True

            event_ids.append(event.id)

            event.category = category
            event.external_link = external_link
            event.review_status = EventReviewStatus.verified
            event.rating = int(item["rating"])
            event.name = item["title"]
            event.description = item["title"]

            start = parse_date_time_str(item['date'])
            update_event_dates_with_recurrence_rule(event, start, None)

            # Place
            place_name = item["location"]
            place_description = ""
            place_location = None

            if 'latitude' in item and 'longitude' in item:
                meeting_point_latitude = item['latitude']
                meeting_point_longitude = item['longitude']
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
            event.status = EventStatus.cancelled if item['canceled'] else EventStatus.scheduled

            if 'categories' in item:
                tag_list = list(item['categories'].values())

                if 'Ausstellung/Kunst' in tag_list:
                    event.category = upsert_event_category('Art')
                elif 'Comedy' in tag_list:
                    event.category = upsert_event_category('Comedy')
                elif 'Konzert/Musik' in tag_list:
                    event.category = upsert_event_category('Music')
                elif 'Theater' in tag_list:
                    event.category = upsert_event_category('Theater')
                elif 'Genuss/Gourmet' in tag_list:
                    event.category = upsert_event_category('Dining')
                elif 'Gesundheit/Wellness' in tag_list:
                    event.category = upsert_event_category('Fitness')
                elif 'Kinder/Jugend' in tag_list:
                    event.category = upsert_event_category('Family')
                elif 'Markt/Flohmarkt' in tag_list:
                    event.category = upsert_event_category('Shopping')
                elif 'Sport' in tag_list:
                    event.category = upsert_event_category('Sports')
                elif 'Vortrag/Lesung' in tag_list:
                    event.category = upsert_event_category('Book')
                elif 'Kabarett' in tag_list:
                    event.category = upsert_event_category('Art')
                elif 'Musical' in tag_list:
                    event.category = upsert_event_category('Theater')
                elif 'Weihnachtsmärkte' in tag_list:
                    event.category = upsert_event_category('Festival')
                elif 'Stadt- und Volksfeste' in tag_list:
                    event.category = upsert_event_category('Festival')

                if 'Kinder/Jugend' in tag_list:
                    event.kid_friendly = True

                tag_list.append('Harzinfo')
                event.tags = ','.join(tag_list)

            print("%s %s %d" % (event.dates[0].start, event.name, event.rating))
            if did_create:
                db.session.add(event)

            db.session.commit()
        except:
            print("Exception")
            pprint(item)

    Event.query.filter(and_(Event.admin_unit_id == admin_unit.id, Event.organizer_id == organizer.id, not_(Event.id.in_(event_ids)))).delete(synchronize_session='fetch')
    db.session.commit()

if __name__ == '__main__':
    for city in cities.values():
        scrape(False, city)
