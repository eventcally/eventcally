from datetime import date, datetime

import pytest
import requests

from project.domain.errors import ExternalCalendarError
from project.infrastructure.services.requests_external_calendar_reader import (
    RequestsExternalCalendarReader,
)

URL = "http://test.de"
START = date(2019, 3, 5)
END = date(2019, 4, 1)


def _read(requests_mock, shared_datadir, filename):
    text = (shared_datadir / filename).read_text()
    requests_mock.get(URL, text=text)
    return RequestsExternalCalendarReader().list_events(URL, START, END)


def test_all_day_holidays(requests_mock, shared_datadir):
    items = _read(requests_mock, shared_datadir, "feiertage-deutschland.ics")

    assert len(items) > 0
    assert all(i.name for i in items)
    assert all(i.allday for i in items)
    assert all(not isinstance(i.start, datetime) for i in items)


def test_recurring_event_with_changed_duration(requests_mock, shared_datadir):
    items = _read(
        requests_mock, shared_datadir, "recurring-events-changed-duration.ics"
    )

    assert len(items) > 1
    assert all(i.name for i in items)
    timed = [i for i in items if not i.allday]
    assert all(isinstance(i.start, datetime) for i in timed)
    assert any(i.allday for i in items)
    durations = {i.end - i.start for i in timed}
    assert len(durations) > 1


def test_http_error_raises_external_calendar_error(requests_mock):
    requests_mock.get(URL, status_code=500)

    with pytest.raises(ExternalCalendarError):
        RequestsExternalCalendarReader().list_events(URL, START, END)


def test_connection_error_raises_external_calendar_error(requests_mock):
    requests_mock.get(URL, exc=requests.exceptions.ConnectionError)

    with pytest.raises(ExternalCalendarError):
        RequestsExternalCalendarReader().list_events(URL, START, END)


def test_invalid_ical_raises_external_calendar_error(requests_mock):
    requests_mock.get(URL, text="not an ical file")

    with pytest.raises(ExternalCalendarError):
        RequestsExternalCalendarReader().list_events(URL, START, END)
