from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateProp, StringProp


class ListDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))
    admin_unit_name = StringProp(lazy_gettext("Organization"))
    created_at = DateProp(lazy_gettext("Created at"))


class UpdateDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))
