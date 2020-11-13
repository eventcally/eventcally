import pytz
from dateutil.rrule import rrulestr
from datetime import datetime
from dateutil.relativedelta import relativedelta

berlin_tz = pytz.timezone("Europe/Berlin")
now = datetime.now(tz=berlin_tz)
today = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)


def create_berlin_date(year, month, day, hour, minute=0):
    return berlin_tz.localize(datetime(year, month, day, hour=hour, minute=minute))


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


def date_set_end_of_day(date):
    return date_add_time(date, hour=23, minute=59, second=59)


def form_input_to_date(date_str, hour=0, minute=0, second=0):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date_time = date_add_time(date, hour=hour, minute=minute, second=second)
    return berlin_tz.localize(date_time)


def form_input_from_date(date):
    return date.strftime("%Y-%m-%d")


def dates_from_recurrence_rule(start, recurrence_rule):
    result = list()

    adv_recurrence_rule = recurrence_rule.replace("T000000", "T235959")
    start_wo_tz = start.replace(tzinfo=None)
    rule_set = rrulestr(adv_recurrence_rule, forceset=True, dtstart=start_wo_tz)

    start_date = start_wo_tz
    end_date = start_date + relativedelta(years=1)
    start_date_begin_of_day = datetime(
        start_date.year, start_date.month, start_date.day
    )
    end_date_end_of_day = datetime(
        end_date.year, end_date.month, end_date.day, hour=23, minute=59, second=59
    )

    for rule_date in rule_set.between(start_date_begin_of_day, end_date_end_of_day):
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
