from flask_babel import lazy_gettext

from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.modular.base_display import BaseDisplay
from project.modular.base_props import (
    BadgePropFormatter,
    BaseProp,
    DateProp,
    EnumProp,
    EventProp,
)


class EventReferenceRequestReviewStatusPropFormatter(BadgePropFormatter):
    badge_mapping = {
        EventReferenceRequestReviewStatus.inbox: "info",
        EventReferenceRequestReviewStatus.rejected: "danger",
        EventReferenceRequestReviewStatus.verified: "success",
    }


class ListDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=EventReferenceRequestReviewStatusPropFormatter(),
    )
    organization = BaseProp(
        lazy_gettext("Organization"),
        keypath="event.admin_unit",
    )
    created_at = DateProp(lazy_gettext("Created at"))
