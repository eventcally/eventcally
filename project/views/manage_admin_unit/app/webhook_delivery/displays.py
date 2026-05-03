from flask import url_for
from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateTimeProp, StringProp


class ReadDisplay(BaseDisplay):
    event_type = StringProp(
        lazy_gettext("Event Type"), keypath="webhook_event.event_type"
    )
    timestamp = DateTimeProp(
        lazy_gettext("Timestamp"), keypath="webhook_event.timestamp"
    )
    organization = StringProp(
        lazy_gettext("Organization"), keypath="app_installation.admin_unit.name"
    )
    webhook_delivery_attempts = StringProp(
        lazy_gettext("Webhook delivery attempts"),
        method_name="get_webhook_delivery_attempts",
        link_method_name="get_webhook_delivery_attempts_link",
    )

    def get_webhook_delivery_attempts(self, object):
        return lazy_gettext("Webhook delivery attempts")

    def get_webhook_delivery_attempts_link(self, object):
        return url_for(
            ".webhook_delivery.webhook_delivery_attempts", webhook_delivery_id=object.id
        )


class ListDisplay(BaseDisplay):
    event_type = StringProp(
        lazy_gettext("Event Type"), keypath="webhook_event.event_type"
    )
    timestamp = DateTimeProp(
        lazy_gettext("Timestamp"), keypath="webhook_event.timestamp"
    )
    organization = StringProp(
        lazy_gettext("Organization"), keypath="app_installation.admin_unit.name"
    )
