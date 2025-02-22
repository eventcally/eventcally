from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateProp, StringProp


class ListDisplay(BaseDisplay):
    organization_name = StringProp(
        lazy_gettext("Organization"), keypath="adminunit.name"
    )
    created_at = DateProp(lazy_gettext("Created at"))
