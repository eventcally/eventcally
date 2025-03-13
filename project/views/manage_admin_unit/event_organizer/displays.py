from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import (
    BoolProp,
    DateProp,
    IntProp,
    LocationProp,
    StringProp,
)


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    location = LocationProp(lazy_gettext("Location"))
    phone = StringProp(lazy_gettext("Phone"))
    email = StringProp(lazy_gettext("Email"))
    url = StringProp(lazy_gettext("Link URL"))
    logo = BoolProp(lazy_gettext("Logo"))
    number_of_events = IntProp(lazy_gettext("Number of events"))
    last_modified_at = DateProp(lazy_gettext("Last modified at"))
