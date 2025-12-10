from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import StringProp


class ListDisplay(BaseDisplay):
    organization_name = StringProp(
        lazy_gettext("Organization"), keypath="admin_unit.name"
    )
