from enum import IntEnum


class EventStatus(IntEnum):
    scheduled = 1
    cancelled = 2
    movedOnline = 3
    postponed = 4
    rescheduled = 5
