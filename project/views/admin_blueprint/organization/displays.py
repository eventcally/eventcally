from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BoolProp, DateProp, StringProp


class ListDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
    is_verified = BoolProp(lazy_gettext("Verified"))
    created_at = DateProp(lazy_gettext("Created at"))
    deletion_requested_at = DateProp(lazy_gettext("Deletion requested at"))


class UpdateDisplay(BaseDisplay):
    name = StringProp(lazy_gettext("Name"))
