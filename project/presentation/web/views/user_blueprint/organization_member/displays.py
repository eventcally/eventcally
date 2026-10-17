from flask_babel import lazy_gettext

from project.presentation.web.modular.base_display import BaseDisplay
from project.presentation.web.modular.base_props import StringProp


class ListDisplay(BaseDisplay):
    organization_name = StringProp(
        lazy_gettext("Organization"), keypath="admin_unit.name"
    )
