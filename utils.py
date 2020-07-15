from dateutil import rrule

BATCH_DELTA = 3 # How many batches to show before + after current batch

def calculate_occurrences(start_date, date_format, rrule_str, start, batch_size):
    # TODO: Return error on failure
    occurrences = []

    rule = rrule.rrulestr(rrule_str, dtstart=start_date)
    iterator = iter(rule)

    cur_batch = start // batch_size
    start = cur_batch * batch_size # Avoid stupid start-values

    if hasattr(rule, '_exdate'):
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
                occurrences.append({'date': exdate.strftime('%Y%m%dT%H%M%S'),
                                    'formattedDate': exdate.strftime(date_format),
                                    'type': 'exdate',})
                i += 1

        if i >= batch_size + start:
            break # We are done!

        i += 1
        if i <= start:
            # We are still iterating up to the first event, so skip this:
            continue

        # Add it to the results
        if date in getattr(rule, '_rdate', []):
            occurrence_type = 'rdate'
        elif date == start_date:
            occurrence_type = 'start'
        else:
            occurrence_type = 'rrule'
        occurrences.append({'date': date.strftime('%Y%m%dT%H%M%S'),
                            'formattedDate': date.strftime(date_format),
                            'type': occurrence_type,})

    while exdates:
        # There are exdates that are after the end of the recurrence.
        # Excluding the last dates make no sense, as you can change the
        # range instead, but we need to support it anyway.
        exdate = exdates.pop(0)
        occurrences.append({'date': exdate.strftime('%Y%m%dT%H%M%S'),
                            'formattedDate': exdate.strftime(date_format),
                            'type': 'exdate',})

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

    max_batch = (num_occurrences - 1)//batch_size
    if last_batch > max_batch:
        last_batch = max_batch
        first_batch = max(0, max_batch - (BATCH_DELTA * 2))

    batches = [((x * batch_size) + 1, (x + 1) * batch_size) for x in range(first_batch, last_batch + 1)]
    batch_data = {'start': start,
                  'end': num_occurrences,
                  'batch_size': batch_size,
                  'batches': batches,
                  'currentBatch': cur_batch - first_batch,
                  }

    return {'occurrences': occurrences, 'batch': batch_data}