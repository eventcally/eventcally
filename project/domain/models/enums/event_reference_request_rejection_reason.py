from enum import IntEnum


class EventReferenceRequestRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4
