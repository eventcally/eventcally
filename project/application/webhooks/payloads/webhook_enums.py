"""Webhook enum types — copies of domain enums to avoid exposing internals."""

from enum import IntEnum


class WebhookEnumBase(IntEnum):
    @classmethod
    def from_domain_enum(cls, enum: IntEnum):
        if enum is None:
            return None
        return cls(enum.value)


class WebhookEventAttendanceMode(WebhookEnumBase):
    offline = 1
    online = 2
    mixed = 3


class WebhookEventPublicStatus(WebhookEnumBase):
    draft = 1
    published = 2
    planned = 3


class WebhookEventStatus(WebhookEnumBase):
    scheduled = 1
    cancelled = 2
    movedOnline = 3
    postponed = 4
    rescheduled = 5


class WebhookEventTargetGroupOrigin(WebhookEnumBase):
    both = 1
    tourist = 2
    resident = 3
