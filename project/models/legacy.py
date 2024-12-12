from enum import IntEnum


class FeaturedEventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class FeaturedEventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4


class EventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
