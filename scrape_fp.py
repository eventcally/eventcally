from app import app, db, get_admin_unit
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
from models import Event, EventStatus, EventCategory, EventPlace, EventOrganizer, AdminUnit

berlin_tz = pytz.timezone('Europe/Berlin')

def scrape(debug = True):
    url = 'https://goslar.feripro.de/programm/40/anmeldung/veranstaltungen'

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

    for js_event in js_assigns['events']:
        event = Event()
        event.admin_unit = get_admin_unit('Stadt Goslar')

        organizer = js_event['organizer']

        name = js_event['name']
        start = parse_date_time_str(js_event['start'])
        end = parse_date_time_str(js_event['end'])
        tag_list = js_event['tags']
        tag_list.append('Ferienpass')
        tags = ','.join(tag_list)
        description = js_event['description']
        kid_friendly = True
        accessible_for_free = js_event['price'] == '0.00'
        external_link = url + '#' + str(js_event['event_id'])

        if js_event['teaser'] and js_event['teaser'] != js_event['description']:
            description = js_event['teaser'] + '\n\n' + description

        if js_event['additional_info']:
            description = description + '\n\n' + js_event['additional_info']

        from_age = None
        if js_event['min_age']:
            from_age = int(js_event['min_age'])

        to_age = None
        if js_event['max_age']:
            to_age = int(js_event['max_age'])

        status = EventStatus.cancelled if js_event['canceled'] else EventStatus.scheduled

        meeting_point = js_event['meeting_point'].replace('\r\n', ', ')

        host_name = js_event['name_public'] if js_event['name_public'] else organizer['name']
        host_phone = js_event['phone_public'] if js_event['phone_public'] else organizer['phone']
        host_email = js_event['email_public'] if js_event['email_public'] else organizer['email']
        host_url = organizer['website'] if organizer['website'] else organizer['facebook']

        print(
            external_link,
            name,
            start,
            end,
            status,
            tags,
            from_age,
            to_age,
            meeting_point,
            js_event['meeting_point_latitude'],
            js_event['meeting_point_longitude'],
            host_name,
            host_phone,
            host_email,
            host_url)

def parse_date_time_str(date_time_str):
    if not date_time_str:
        return None

    date_time = datetime.datetime.fromisoformat(date_time_str)
    return berlin_tz.localize(date_time)

if __name__ == '__main__':
    scrape()