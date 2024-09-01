from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import LocationProp, MethodProp, StringProp


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    location = LocationProp(lazy_gettext("Location"))
    has_coordinates = MethodProp("get_has_coordinates", lazy_gettext("Coordinates"))
    has_photo = MethodProp("get_has_photo", lazy_gettext("Photo"))
    number_of_events = MethodProp(
        "get_number_of_events", lazy_gettext("Number of events")
    )

    def get_has_coordinates(self, object):
        return True if object.location and object.location.coordinate else False

    def get_has_photo(self, object):
        return True if object.photo else False

    def get_number_of_events(self, object):
        return len(object.events)
