from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import BoolProp, DateProp, StringProp


class ListDisplay(BaseDisplay):
    organization = StringProp(
        lazy_gettext("Organization"), keypath="target_admin_unit.name"
    )
    verify = BoolProp(lazy_gettext("Verify other organization"))
    auto_verify_event_reference_requests = BoolProp(
        lazy_gettext("Verify reference requests automatically")
    )
    last_modified_at = DateProp(lazy_gettext("Last modified at"))


class UpdateDisplay(BaseDisplay):
    organization = StringProp(
        lazy_gettext("Organization"), keypath="target_admin_unit.name"
    )
