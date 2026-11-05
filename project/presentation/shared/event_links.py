from urllib.parse import quote_plus

from flask import url_for

from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.shared.dateutils import berlin_tz, round_to_next_day
from project.shared.utils import get_place_str


def get_share_links(url: str, title: str) -> dict:
    share_links = dict()
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(title)

    share_links["facebook"] = (
        f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
    )
    share_links["twitter"] = (
        f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_title}"
    )
    share_links["email"] = f"mailto:?subject={encoded_title}&body={encoded_url}"
    share_links["whatsapp"] = f"whatsapp://send?text={encoded_url}"
    share_links["telegram"] = f"https://t.me/share/url?url={encoded_url}"
    share_links["url"] = url

    return share_links


def get_calendar_links_for_event_date(event_date) -> dict:
    calendar_links = dict()

    url = url_for("main.event_date", id=event_date.id, _external=True)
    encoded_url = quote_plus(url)
    encoded_title = quote_plus(event_date.event.name)
    encoded_timezone = quote_plus(berlin_tz.key)

    start_date = event_date.start
    end_date = event_date.end if event_date.end else start_date
    date_format = "%Y%m%dT%H%M%S"

    if event_date.allday:
        date_format = "%Y%m%d"
        end_date = round_to_next_day(end_date)

    start = start_date.astimezone(berlin_tz).strftime(date_format)
    end = end_date.astimezone(berlin_tz).strftime(date_format)

    if (
        event_date.event.attendance_mode
        and event_date.event.attendance_mode != EventAttendanceMode.online
    ):
        location = get_place_str(event_date.event.event_place)
        locationParam = f"&location={quote_plus(location)}"
    else:
        locationParam = ""

    calendar_links["google"] = (
        f"http://www.google.com/calendar/event?action=TEMPLATE&text={encoded_title}&dates={start}/{end}&ctz={encoded_timezone}&details={encoded_url}{locationParam}"
    )

    calendar_links["ics"] = url_for(
        "main.event_date_ical", id=event_date.id, _external=True
    )

    return calendar_links


def get_calendar_links_for_event(event) -> dict:
    calendar_links = dict()
    calendar_links["ics"] = url_for("main.event_ical", id=event.id, _external=True)
    return calendar_links
