from datetime import date, datetime
from typing import List

import icalendar
import recurring_ical_events
import requests

from project.application.read_models.external_calendar_read_models import (
    ExternalCalendarEventReadModel,
)
from project.application.services.abstract_external_calendar_reader import (
    AbstractExternalCalendarReader,
)
from project.domain.errors import ExternalCalendarError
from project.shared.utils import decode_response_content

REQUEST_TIMEOUT_SECONDS = 10


class RequestsExternalCalendarReader(AbstractExternalCalendarReader):
    def list_events(
        self, url: str, start: date, end: date
    ) -> List[ExternalCalendarEventReadModel]:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            ical_string = decode_response_content(response)
            calendar = icalendar.Calendar.from_ical(ical_string)
            events = recurring_ical_events.of(calendar).between(start, end)
        except Exception as e:
            raise ExternalCalendarError() from e

        items = list()

        for event in events:
            summary = event.get("SUMMARY")
            dt_start = event.get("DTSTART")
            dt_end = event.get("DTEND")
            location = event.get("LOCATION")
            description = event.get("DESCRIPTION")

            if not summary or not dt_start:  # pragma: no cover
                continue

            event_start = dt_start.dt
            items.append(
                ExternalCalendarEventReadModel(
                    name=str(summary),
                    start=event_start,
                    end=dt_end.dt if dt_end else None,
                    allday=not isinstance(event_start, datetime),
                    location=str(location) if location else None,
                    description=str(description) if description else None,
                )
            )

        return items
