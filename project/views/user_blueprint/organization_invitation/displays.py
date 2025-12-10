from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateProp, StringProp


class ListDisplay(BaseDisplay):
    organization_name = StringProp(
        lazy_gettext("Organization"), keypath="admin_unit.name"
    )
    name = StringProp(lazy_gettext("Name"), keypath="admin_unit_name")
    created_at = DateProp(lazy_gettext("Created at"))


class UpdateDisplay(BaseDisplay):
    email = StringProp(lazy_gettext("Email"))
