from flask import url_for
from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BaseProp, DateProp, EventProp


class ReadDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"), link_method_name="get_event_link")
    rating = BaseProp(lazy_gettext("Rating"), method_name="get_rating")

    def get_rating(self, object):
        return "%d/10" % (object.rating / 10) if object.rating else None

    def should_show_audit(self, object):
        return True

    def should_audit_show_user(self, object):
        return True

    def get_event_link(self, object):
        return url_for(
            "event",
            event_id=object.event.id,
        )


class ListDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"))
    organization = BaseProp(lazy_gettext("Organization"), keypath="event.admin_unit")
    created_at = DateProp(lazy_gettext("Created at"))
