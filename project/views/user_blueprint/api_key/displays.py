from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateProp, StringProp


class ReadDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    created_at = DateProp(lazy_gettext("Created at"))


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    created_at = DateProp(lazy_gettext("Created at"))
