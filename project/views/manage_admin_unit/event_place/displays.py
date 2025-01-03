from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BoolProp, CountProp, LocationProp, StringProp


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    location = LocationProp(lazy_gettext("Location"))
    coordinates = BoolProp(lazy_gettext("Coordinates"), keypath="location.coordinate")
    photo = BoolProp(lazy_gettext("Photo"))
    events = CountProp(lazy_gettext("Number of events"))
