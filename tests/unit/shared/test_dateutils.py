def test_calculate_occurrences():
    result = get_calculate_occurrences("RRULE:FREQ=DAILY;COUNT=7")
    assert result["batch"]["batch_size"] == 10

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 7

    occurence = result["occurrences"][0]
    assert occurence["date"] == "20300101T000000"
    assert occurence["formattedDate"] == '"01.01.2030"'


def test_calculate_occurrences_exdate():
    result = get_calculate_occurrences(
        "RRULE:FREQ=DAILY;COUNT=2\nEXDATE:20300102T000000"
    )

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 2


def test_calculate_occurrences_rdate():
    result = get_calculate_occurrences(
        "RRULE:FREQ=DAILY;COUNT=2\nEXDATE:20300102T000000\nRDATE:20300103T000000"
    )

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 3


def test_calculate_occurrences_exdateStart():
    result = get_calculate_occurrences(
        "RRULE:FREQ=DAILY;COUNT=20\nEXDATE:20300102T000000", 10
    )

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 10


def test_calculate_occurrences_exdateBefore():
    result = get_calculate_occurrences(
        "RRULE:FREQ=DAILY;COUNT=20\nEXDATE:20290102T000000", 10
    )

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 10


def test_calculate_occurrences_count():
    result = get_calculate_occurrences("RRULE:FREQ=DAILY;COUNT=100")

    number_of_occurences = len(result["occurrences"])
    assert number_of_occurences == 10


def get_calculate_occurrences(rrule_str, start=0):
    from datetime import datetime

    from project.shared.dateutils import calculate_occurrences

    start_date = datetime(2030, 1, 1)
    date_format = '"%d.%m.%Y"'
    batch_size = 10

    return calculate_occurrences(start_date, date_format, rrule_str, start, batch_size)


def test_get_now_and_today():
    from project.shared.dateutils import berlin_tz, get_now, get_today

    now = get_now()
    today = get_today()

    assert now.tzinfo == berlin_tz
    assert (today.hour, today.minute, today.second) == (0, 0, 0)
    assert today.date() == now.date()


def test_create_berlin_date():
    from project.shared.dateutils import berlin_tz, create_berlin_date

    date = create_berlin_date(2030, 1, 2, 3, 4, 5)
    assert date.isoformat() == "2030-01-02T03:04:05+01:00"
    assert date.tzinfo == berlin_tz


def test_date_parts_are_equal():
    from datetime import datetime

    from project.shared.dateutils import date_parts_are_equal

    assert date_parts_are_equal(datetime(2030, 1, 2, 3), datetime(2030, 1, 2, 22))
    assert not date_parts_are_equal(datetime(2030, 1, 2), datetime(2030, 1, 3))


def test_date_set_begin_and_end_of_day():
    from project.shared.dateutils import (
        create_berlin_date,
        date_set_begin_of_day,
        date_set_end_of_day,
    )

    date = create_berlin_date(2030, 1, 2, 12, 30)

    assert date_set_begin_of_day(date) == create_berlin_date(2030, 1, 2)
    assert date_set_end_of_day(date) == create_berlin_date(2030, 1, 2, 23, 59, 59)
    assert date_set_begin_of_day(date, remove_tz=True).tzinfo is None
    assert date_set_end_of_day(date, remove_tz=True).tzinfo is None


def test_round_to_next_day_and_full_hour():
    from project.shared.dateutils import (
        create_berlin_date,
        round_to_next_day,
        round_to_next_full_hour,
    )

    date = create_berlin_date(2030, 1, 2, 12, 30)

    assert round_to_next_day(date) == create_berlin_date(2030, 1, 3)
    assert round_to_next_full_hour(date) == create_berlin_date(2030, 1, 2, 13)


def test_get_next_full_hour():
    from project.shared.dateutils import get_next_full_hour, get_now

    result = get_next_full_hour()
    assert (result.minute, result.second) == (0, 0)
    assert 0 < (result - get_now()).total_seconds() <= 3600


def test_form_input_to_and_from_date():
    from project.shared.dateutils import (
        create_berlin_date,
        form_input_from_date,
        form_input_to_date,
    )

    assert form_input_to_date("2030-01-02", hour=5) == create_berlin_date(2030, 1, 2, 5)
    assert form_input_from_date(create_berlin_date(2030, 1, 2)) == "2030-01-02"
    assert form_input_from_date(None) == ""


def test_create_icalendar():
    from project.shared.dateutils import create_icalendar

    ical = create_icalendar().to_ical().decode("utf-8")

    assert "X-WR-TIMEZONE:Europe/Berlin" in ical
    assert "TZNAME:CET" in ical
    assert "TZNAME:CEST" in ical
