from flask_babel import lazy_gettext

from project.presentation.web.modular.base_display import BaseDisplay
from project.presentation.web.modular.base_props import (
    BoolProp,
    DateProp,
    IntProp,
    LocationProp,
    StringProp,
)


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    location = LocationProp(lazy_gettext("Location"))
    coordinates = BoolProp(lazy_gettext("Coordinates"), keypath="has_coordinates")
    photo = BoolProp(lazy_gettext("Photo"), keypath="has_photo")
    number_of_events = IntProp(lazy_gettext("Number of events"))
    last_modified_at = DateProp(lazy_gettext("Last modified at"))
