from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrulestr

berlin_tz = pytz.timezone("Europe/Berlin")


def get_now():
    return datetime.now(tz=berlin_tz)


def get_today():
    now = get_now()
    return datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)


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


def dates_from_recurrence_rule(start, recurrence_rule):
    result = []

    start_begin_of_day = date_set_begin_of_day(start, remove_tz=True)
    rule_set = rrulestr(recurrence_rule, forceset=True, dtstart=start_begin_of_day)

    today = get_today()
    start_date = today if today > start else start
    start_date_begin_of_day = date_set_begin_of_day(start_date, remove_tz=True)

    end_date = start_date_begin_of_day + relativedelta(years=1)
    end_date_end_of_day = date_set_end_of_day(end_date, remove_tz=True)

    for rule_date in rule_set.between(
        start_date_begin_of_day, end_date_end_of_day, inc=True
    ):
        rule_data_w_tz = berlin_tz.localize(rule_date)
        result.append(rule_data_w_tz)

    return result
