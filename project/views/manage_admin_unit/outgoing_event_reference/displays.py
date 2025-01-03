from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BaseProp, DateProp, EventProp


class ListDisplay(BaseDisplay):
    event = EventProp(lazy_gettext("Event"))
    admin_unit = BaseProp(lazy_gettext("Organization"))
    created_at = DateProp(lazy_gettext("Created at"))
