from urllib.parse import urlparse

import requests
from sqlalchemy import and_

from project.models import Event, EventOrganizer, EventPlace
from project.services.importer.ld_json_importer import LdJsonImporter
from project.utils import decode_response_content


class EventImporter:
    def __init__(self, admin_unit_id: int):
        self.admin_unit_id = admin_unit_id

    def load_event_from_url(self, absolute_url: str):
        sanitized_url = self._sanitize_url(absolute_url)
        headers = dict()

        if "eventim.de" in absolute_url:
            headers[
                "User-Agent"
            ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

        response = requests.get(sanitized_url, headers=headers)
        html = decode_response_content(response)
        return self.load_event_from_html(html, absolute_url)

    def load_event_from_html(self, html: str, origin_url: str):
        importer = LdJsonImporter(html, origin_url)
        event = importer.load_event()

        event.admin_unit_id = self.admin_unit_id
        self._match_organizer(event)
        self._match_place(event)
        return event

    def _match_organizer(self, event: Event):
        organizer = EventOrganizer.query.filter(
            and_(
                EventOrganizer.admin_unit_id == self.admin_unit_id,
                EventOrganizer.name == event.organizer.name,
            )
        ).first()

        if organizer:
            event.organizer = organizer
        else:
            event.organizer.admin_unit_id = self.admin_unit_id

    def _match_place(self, event: Event):
        place = EventPlace.query.filter(
            and_(
                EventPlace.admin_unit_id == self.admin_unit_id,
                EventPlace.name == event.event_place.name,
            )
        ).first()

        if place:
            event.event_place = place
        else:
            event.event_place.admin_unit_id = self.admin_unit_id

    def _sanitize_url(self, absolute_url: str) -> str:
        result = absolute_url

        try:
            p = urlparse(absolute_url)

            if p.hostname.endswith(".reservix.de"):
                result = p._replace(
                    netloc=p.netloc.replace(p.hostname, "www.reservix.de")
                ).geturl()

            if p.hostname == "www.facebook.com":
                result = p._replace(
                    netloc=p.netloc.replace("www.facebook.com", "m.facebook.com")
                ).geturl()
        except Exception:  # pragma: no cover
            pass

        return result
