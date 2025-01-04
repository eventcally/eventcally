from flask import url_for
from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BaseProp, DateProp, EnumProp, EventProp
from project.views.manage_admin_unit.incoming_event_reference_request.displays import (
    EventReferenceRequestReviewStatusPropFormatter,
)


class ReadDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"), link_method_name="get_event_link")
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=EventReferenceRequestReviewStatusPropFormatter(),
    )
    rejection_reason = EnumProp(lazy_gettext("Rejection reason"), hide_when_empty=True)
    admin_unit = BaseProp(lazy_gettext("Organization"))

    def get_event_link(self, object):
        return url_for(
            "event",
            event_id=object.event.id,
        )


class ListDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=EventReferenceRequestReviewStatusPropFormatter(),
    )
    admin_unit = BaseProp(lazy_gettext("Organization"))
    created_at = DateProp(lazy_gettext("Created at"))
