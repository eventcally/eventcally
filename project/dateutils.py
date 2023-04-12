from datetime import datetime, timedelta

import icalendar
import pytz
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrulestr

berlin_tz = pytz.timezone("Europe/Berlin")
gmt_tz = pytz.timezone("GMT")


def get_now():
    return datetime.now(tz=berlin_tz)


def get_today():
    now = get_now()
    return datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)


def create_berlin_date(year, month, day, hour=0, minute=0, second=0):
    return berlin_tz.localize(
        datetime(year, month, day, hour=hour, minute=minute, second=second)
    )


def date_parts_are_equal(date1: datetime, date2: datetime) -> bool:
    return (
        date1.year == date2.year
        and date1.month == date2.month
        and date1.day == date2.day
    )


def date_add_time(date, hour=0, minute=0, second=0, tzinfo=None):
    return datetime(
        date.year,
        date.month,
        date.day,
        hour=hour,
        minute=minute,
        second=second,
        tzinfo=tzinfo,
    )


def date_set_begin_of_day(date, remove_tz=False):
    tzinfo = None if remove_tz else date.tzinfo
    return date_add_time(date, tzinfo=tzinfo)


def date_set_end_of_day(date, remove_tz=False):
    tzinfo = None if remove_tz else date.tzinfo
    return date_add_time(date, hour=23, minute=59, second=59, tzinfo=tzinfo)


def round_to_next_day(date):
    new_date = date + timedelta(days=1)
    return date_set_begin_of_day(new_date)


def round_to_next_full_hour(date):
    new_date = date + timedelta(hours=1)
    return date_add_time(date, new_date.hour, tzinfo=date.tzinfo)


def get_next_full_hour():
    now = get_now()
    return round_to_next_full_hour(now)


def form_input_to_date(date_str, hour=0, minute=0, second=0):
    if not date_str:  # pragma: no cover
        return None
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date_time = date_add_time(date, hour=hour, minute=minute, second=second)
    return berlin_tz.localize(date_time)


def form_input_from_date(date):
    return date.strftime("%Y-%m-%d") if date else ""


def parse_iso_string(input: str) -> datetime:
    return isoparse(input)


def dates_from_recurrence_rule(start, recurrence_rule):
    result = list()

    start_begin_of_day = date_set_begin_of_day(start, remove_tz=True)
    rule_set = rrulestr(recurrence_rule, forceset=True, dtstart=start_begin_of_day)

    # Keine Daten in der Vergangenheit erstellen
    today = get_today()
    start_date = today if today > start else start
    start_date_begin_of_day = date_set_begin_of_day(start_date, remove_tz=True)

    # Max. 1 Jahr in die Zukunft
    end_date = start_date_begin_of_day + relativedelta(years=1)
    end_date_end_of_day = date_set_end_of_day(end_date, remove_tz=True)

    for rule_date in rule_set.between(
        start_date_begin_of_day, end_date_end_of_day, inc=True
    ):
        rule_data_w_tz = berlin_tz.localize(rule_date)
        result.append(rule_data_w_tz)

    return result


BATCH_DELTA = 3  # How many batches to show before + after current batch


def calculate_occurrences(start_date, date_format, rrule_str, start, batch_size):
    # TODO: Return error on failure
    occurrences = []

    rule = rrulestr(rrule_str, dtstart=start_date)
    iterator = iter(rule)

    cur_batch = start // batch_size
    start = cur_batch * batch_size  # Avoid stupid start-values

    if hasattr(rule, "_exdate"):
        exdates = sorted(rule._exdate)
    else:
        exdates = []

    # Loop through the start first dates, to skip them:
    i = 0
    occurrences = []
    while True:
        try:
            # Get a date
            date = next(iterator)
        except StopIteration:
            # No more dates
            break
        while exdates and date > exdates[0]:
            # There are exdates that appear before this date:
            if i < start:
                # Skip them
                exdates.pop(0)
                i += 1
            else:
                # include them
                exdate = exdates.pop(0)
                occurrences.append(
                    {
                        "date": exdate.strftime("%Y%m%dT%H%M%S"),
                        "formattedDate": exdate.strftime(date_format),
                        "type": "exdate",
                    }
                )
                i += 1

        if i >= batch_size + start:
            break  # We are done!

        i += 1
        if i <= start:
            # We are still iterating up to the first event, so skip this:
            continue

        # Add it to the results
        if date in getattr(rule, "_rdate", []):
            occurrence_type = "rdate"
        elif date == start_date:
            occurrence_type = "start"
        else:
            occurrence_type = "rrule"
        occurrences.append(
            {
                "date": date.strftime("%Y%m%dT%H%M%S"),
                "formattedDate": date.strftime(date_format),
                "type": occurrence_type,
            }
        )

    while exdates:
        # There are exdates that are after the end of the recurrence.
        # Excluding the last dates make no sense, as you can change the
        # range instead, but we need to support it anyway.
        exdate = exdates.pop(0)
        occurrences.append(
            {
                "date": exdate.strftime("%Y%m%dT%H%M%S"),
                "formattedDate": exdate.strftime(date_format),
                "type": "exdate",
            }
        )

    # Calculate no of occurrences, but only to a max of three times
    # the batch size. This will support infinite recurrence in a
    # useable way, as there will always be more batches.
    first_batch = max(0, cur_batch - BATCH_DELTA)
    last_batch = max(BATCH_DELTA * 2, cur_batch + BATCH_DELTA)
    maxcount = (batch_size * last_batch) - start

    num_occurrences = 0
    while True:
        try:
            next(iterator)
            num_occurrences += 1
        except StopIteration:
            break
        if num_occurrences >= maxcount:
            break

    # Total number of occurrences:
    num_occurrences += batch_size + start

    max_batch = (num_occurrences - 1) // batch_size
    if last_batch > max_batch:
        last_batch = max_batch
        first_batch = max(0, max_batch - (BATCH_DELTA * 2))

    batches = [
        ((x * batch_size) + 1, (x + 1) * batch_size)
        for x in range(first_batch, last_batch + 1)
    ]
    batch_data = {
        "start": start,
        "end": num_occurrences,
        "batch_size": batch_size,
        "batches": batches,
        "currentBatch": cur_batch - first_batch,
    }

    return {"occurrences": occurrences, "batch": batch_data}


def create_icalendar() -> icalendar.Calendar:
    cal = icalendar.Calendar()
    cal.add("prodid", "-//eventcally//github.com/eventcally/eventcally//")
    cal.add("version", "2.0")
    cal.add("x-wr-timezone", berlin_tz.zone)

    tzc = icalendar.Timezone()
    tzc.add("tzid", berlin_tz.zone)
    tzc.add("x-lic-location", berlin_tz.zone)

    tzs = icalendar.TimezoneStandard()
    tzs.add("tzname", "CET")
    tzs.add("dtstart", datetime(1970, 10, 25, 3, 0, 0))
    tzs.add("rrule", {"freq": "yearly", "bymonth": 10, "byday": "-1su"})
    tzs.add("TZOFFSETFROM", timedelta(hours=2))
    tzs.add("TZOFFSETTO", timedelta(hours=1))

    tzd = icalendar.TimezoneDaylight()
    tzd.add("tzname", "CEST")
    tzd.add("dtstart", datetime(1970, 3, 29, 2, 0, 0))
    tzd.add("rrule", {"freq": "yearly", "bymonth": 3, "byday": "-1su"})
    tzd.add("TZOFFSETFROM", timedelta(hours=1))
    tzd.add("TZOFFSETTO", timedelta(hours=2))

    tzc.add_component(tzs)
    tzc.add_component(tzd)
    cal.add_component(tzc)

    return cal
