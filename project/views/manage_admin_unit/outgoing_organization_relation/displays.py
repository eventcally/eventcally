from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import StringProp


class ListDisplay(BaseDisplay):
    organization = StringProp(
        lazy_gettext("Organization"), keypath="target_admin_unit.name"
    )


class UpdateDisplay(BaseDisplay):
    organization = StringProp(
        lazy_gettext("Organization"), keypath="target_admin_unit.name"
    )
