import json

import validators
from bs4 import BeautifulSoup

from project.dateutils import parse_iso_string
from project.imageutils import (
    get_bytes_from_image,
    get_image_from_url,
    get_mime_type_from_image,
    resize_image_to_max,
    resize_image_to_min,
    validate_image,
)
from project.models import (
    Event,
    EventAttendanceMode,
    EventCategory,
    EventDateDefinition,
    EventOrganizer,
    EventPlace,
    EventStatus,
    Image,
    Location,
)


class LdJsonImporter:
    def __init__(self, html: str, origin_url: str):
        self.html = html
        self.origin_url = origin_url
        self.event_type_mapping = {
            "ChildrensEvent": "Family",
            "ComedyEvent": "Comedy",
            "DanceEvent": "Dance",
            "EducationEvent": "Lecture",
            "ExhibitionEvent": "Exhibition",
            "Festival": "Festival",
            "FoodEvent": "Dining",
            "LiteraryEvent": "Book",
            "MusicEvent": "Music",
            "SportsEvent": "Sports",
            "TheaterEvent": "Theater",
        }
        self.event_status_mapping = {
            "EventScheduled": EventStatus.scheduled,
            "EventCancelled": EventStatus.cancelled,
            "EventMovedOnline": EventStatus.movedOnline,
            "EventPostponed": EventStatus.postponed,
            "EventRescheduled": EventStatus.rescheduled,
        }
        self.event_attendance_mode_mapping = {
            "OfflineEventAttendanceMode": EventAttendanceMode.offline,
            "OnlineEventAttendanceMode": EventAttendanceMode.online,
            "MixedEventAttendanceMode": EventAttendanceMode.mixed,
        }

    def load_event(self):
        self.ld_json = self.load_ld_json_from_html()
        return self.load_event_from_ld_json()

    def load_ld_json_from_html(self):
        self.soup = BeautifulSoup(self.html, features="html.parser")
        ld_json_scripts = self.soup.find_all("script", {"type": "application/ld+json"})

        for ld_json_script in ld_json_scripts:
            try:
                ld_json = self._load_ld_json_from_script(ld_json_script)
                if ld_json:
                    break
            except Exception:
                pass

        ld_json = self._strip_ld_json(ld_json)

        if "description" in ld_json:
            desc_soup = BeautifulSoup(ld_json["description"], features="html.parser")
            for br in desc_soup.find_all("br"):
                br.replace_with("\n" + br.text)
            ld_json["description"] = desc_soup.text

        if "harzinfo.de" in self.origin_url:
            coordinate_div = self.soup.find("div", attrs={"data-position": True})
            if coordinate_div:
                ld_json["coordinate"] = coordinate_div["data-position"]

        return ld_json

    def load_event_from_ld_json(self):
        item = self.ld_json

        event = Event()
        self.event = event

        event.name = item["name"]

        if "url" in item and validators.url(item["url"]):
            event.external_link = item["url"]
        else:
            event.external_link = self.origin_url

        self._load_organizer()
        self._load_place()
        self._load_event_status()
        self._load_date_definition()
        self._add_categories()
        self._add_tags()
        self._load_event_photo()
        self._load_attendance_mode()

        if "description" in item:
            event.description = item["description"]

        if "isAccessibleForFree" in item:
            event.accessible_for_free = item["isAccessibleForFree"]

        return event

    def _load_date_definition(self):
        event = self.event
        item = self.ld_json

        definition = EventDateDefinition()
        definition.start = parse_iso_string(item["startDate"])

        if "endDate" in item:
            definition.end = parse_iso_string(item["endDate"])

        event.date_definitions = [definition]

    def _load_organizer(self):
        event = self.event
        item = self.ld_json
        organizer_item = None

        if "organizer" in item:
            organizer_item = item["organizer"]

        if not organizer_item and "author" in item:
            organizer_item = item["author"]

        if (
            organizer_item
            and isinstance(organizer_item, list)
            and len(organizer_item) > 0
            and organizer_item[0]
        ):
            organizer_item = organizer_item[0]

        if organizer_item:
            event.organizer = self._load_organizer_from_ld_json(organizer_item)
        else:
            event.organizer = self._load_organizer_from_html()

        if not event.organizer:
            raise Exception("Organizer is missing")

    def _load_organizer_from_ld_json(self, organizer_item: dict) -> EventOrganizer:
        organizer = EventOrganizer()

        organizer.name = organizer_item["name"]

        if "url" in organizer_item and validators.url(organizer_item["url"]):
            organizer.url = organizer_item["url"]

        if "email" in organizer_item and validators.email(organizer_item["email"]):
            organizer.email = organizer_item["email"]

        if "telephone" in organizer_item:
            organizer.phone = organizer_item["telephone"]

        if "faxNumber" in organizer_item:
            organizer.fax = organizer_item["faxNumber"]

        if "address" in organizer_item:
            organizer.location = self._load_location(organizer_item["address"])

        return organizer

    def _load_organizer_from_html(self) -> EventOrganizer:
        if "reservix.de" in self.origin_url:
            div = self.soup.find("div", attrs={"class": "c-organizer-info"})

            if div:
                prefix = "Veranstalter:"
                text = div.text.strip()

                if text.startswith(prefix):
                    organizer_text = text[len(prefix) :].strip()
                    organizer = self._load_organizer_from_text(organizer_text)

                    if organizer:
                        return organizer

        if "eventim.de" in self.origin_url:
            div = self.soup.find(
                "div", attrs={"data-qa": "additional-info-promoter-content"}
            )

            if div:
                header_div = div.find(
                    lambda tag: tag.name == "div" and "Veranstalter:" in tag.text
                )

                if header_div:
                    organizer_paragraph = header_div.findNext("p")

                    if organizer_paragraph:
                        organizer_text = organizer_paragraph.text.strip()
                        organizer = self._load_organizer_from_text(organizer_text)

                        if organizer:
                            return organizer

        if "regiondo.de" in self.origin_url:
            span = self.soup.find(
                "span", attrs={"itemtype": "http://schema.org/Organization"}
            )

            if span:
                organizer_text = span.text.strip()
                organizer = self._load_organizer_from_text(organizer_text)

                if organizer:
                    return organizer

        if "facebook.com" in self.origin_url:
            anchor = self.soup.find("a", attrs={"class": "cc"})

            if anchor:
                organizer_text = anchor.text.strip()
                organizer = self._load_organizer_from_text(organizer_text)

                if organizer:
                    return organizer

        return None

    def _load_organizer_from_text(self, organizer_text: str) -> EventOrganizer:
        organizer_parts = organizer_text.split(",")

        organizer = EventOrganizer()
        organizer.name = organizer_parts[0].strip()

        if len(organizer_parts) == 4:
            location = Location()
            location.street = organizer_parts[1].strip()
            location.city = organizer_parts[2].strip()
            location.country = organizer_parts[3].strip()

            if " " in location.city:
                city_parts = location.city.split(" ")
                location.postalCode = city_parts[0]
                location.city = city_parts[1]

            organizer.location = location

        return organizer

    def _load_place(self):
        event = self.event
        item = self.ld_json
        place_item = None

        if "location" in item:
            place_item = item["location"]

            if isinstance(place_item, list) and len(place_item) > 0 and place_item[0]:
                place_item = place_item[0]

        location_type = place_item["@type"] if "@type" in place_item else None

        place = EventPlace()

        if "name" not in place_item and location_type == "VirtualLocation":
            place.name = "Online"
        else:
            place.name = place_item["name"]

        location = Location()

        if "address" in place_item:
            location = self._load_location(place_item["address"])

        if "geo" in place_item:
            geo_item = place_item["geo"]

            if (
                "@type" in geo_item
                and geo_item["@type"] == "GeoCoordinates"
                and "latitude" in geo_item
                and "longitude" in geo_item
            ):
                latitude = float(geo_item["latitude"])
                longitude = float(geo_item["longitude"])
                if latitude != 0 and longitude != 0:
                    location.latitude = latitude
                    location.longitude = longitude

        if "coordinate" in item:
            lat_str, lon_str = item["coordinate"].split(",")
            latitude = float(lat_str)
            longitude = float(lon_str)
            if latitude != 0 and longitude != 0:
                location.latitude = latitude
                location.longitude = longitude

        if "url" in place_item and validators.url(place_item["url"]):
            place.url = place_item["url"]

        place.location = location
        event.event_place = place

    def _load_location(self, address: dict) -> Location:
        location = Location()

        if "streetAddress" in address:
            location.street = address["streetAddress"]

        if "postalCode" in address:
            location.postalCode = address["postalCode"]

        if "addressLocality" in address:
            location.city = address["addressLocality"]

        if "addressCountry" in address:
            location.country = address["addressCountry"]

        return location

    def _load_event_photo(self):
        event = self.event
        item = self.ld_json

        if "image" not in item:
            return

        image = item["image"]

        if isinstance(image, list) and len(image) == 0:
            return

        image_items = image if isinstance(image, list) else [image]

        for image_item in image_items:

            if isinstance(image_item, str):
                image_item = {"url": image_item}

            if "url" not in image_item:
                continue

            try:
                pillow_image = get_image_from_url(image_item["url"])
                encoding_format = get_mime_type_from_image(pillow_image)

                if pillow_image.width > 200 or pillow_image.height > 200:
                    pillow_image = resize_image_to_min(pillow_image)

                validate_image(pillow_image)
                resize_image_to_max(pillow_image)
                data = get_bytes_from_image(pillow_image)
            except Exception:
                continue

            image = Image()
            image.data = data
            image.encoding_format = encoding_format

            if "contributor" in image_item:
                image.copyright_text = image_item["contributor"]

            event.photo = image
            return

    def _load_event_status(self):
        event = self.event
        item = self.ld_json

        if "eventStatus" in item:
            eventStatus = self._get_item_enum_value("eventStatus")

            if eventStatus in self.event_status_mapping:
                event.status = self.event_status_mapping[eventStatus]
                return

            if eventStatus == "ausgebucht":
                event.booked_up = True

        event.status = EventStatus.scheduled

    def _load_attendance_mode(self):
        event = self.event
        item = self.ld_json

        if "eventAttendanceMode" in item:
            eventAttendanceMode = self._get_item_enum_value("eventAttendanceMode")

            if eventAttendanceMode in self.event_attendance_mode_mapping:
                event.attendance_mode = self.event_attendance_mode_mapping[
                    eventAttendanceMode
                ]

    def _add_categories(self):
        event = self.event
        item = self.ld_json
        types_value = item["@type"]
        types_list = types_value if isinstance(types_value, list) else [types_value]

        event_categories = list()

        for item_type in types_list:
            if item_type in self.event_type_mapping:
                category_name = self.event_type_mapping[item_type]
                category = EventCategory.query.filter(
                    EventCategory.name == category_name
                ).first()
                if category:
                    event_categories.append(category)

        if len(event_categories) > 0:
            event.categories = event_categories

    def _add_tags(self):
        event = self.event
        item = self.ld_json

        if "keywords" not in item:
            return

        tags = list()

        for keyword in item["keywords"].split(","):
            keyword = keyword.strip()
            if not keyword[0].islower():
                tags.append(keyword)

        if len(tags) > 0:
            event.tags = ",".join(tags)

    def _load_ld_json_from_script(self, ld_json_script):
        ld_json_object = json.loads(ld_json_script.string)
        ld_json = (
            ld_json_object[0] if isinstance(ld_json_object, list) else ld_json_object
        )

        types_value = ld_json["@type"]
        types_list = types_value if isinstance(types_value, list) else [types_value]

        for type in types_list:
            if type.endswith("Event"):
                return ld_json

        return None

    def _strip_ld_json(self, value: any) -> any:
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, dict):
            result = dict()
            for k, v in value.items():
                if v:
                    result[k] = self._strip_ld_json(v)
            return result

        if isinstance(value, list):
            result = list()
            for elem in value:
                if elem:
                    result.append(self._strip_ld_json(elem))
            return result

        return value

    def _get_item_enum_value(self, key: str) -> str:
        return (
            self.ld_json[key]
            .replace("http://schema.org/", "")
            .replace("https://schema.org/", "")
        )
