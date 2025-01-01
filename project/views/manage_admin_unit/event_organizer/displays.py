from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import LocationProp, MethodProp, StringProp


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    location = LocationProp(lazy_gettext("Location"))
    phone = StringProp(lazy_gettext("Phone"))
    email = StringProp(lazy_gettext("Email"))
    url = StringProp(lazy_gettext("Link URL"))
    has_logo = MethodProp("get_has_logo", lazy_gettext("Logo"))
    number_of_events = MethodProp(
        "get_number_of_events", lazy_gettext("Number of events")
    )

    def get_has_logo(self, object):
        return True if object.logo else False

    def get_number_of_events(self, object):
        return len(object.events)
