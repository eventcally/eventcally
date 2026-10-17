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

    from project.dateutils import calculate_occurrences

    start_date = datetime(2030, 1, 1)
    date_format = '"%d.%m.%Y"'
    batch_size = 10

    return calculate_occurrences(start_date, date_format, rrule_str, start, batch_size)
