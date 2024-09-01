from flask_babel import gettext, lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import DateTimeProp, MethodProp, StringProp


class ListDisplay(BaseDisplay):
    id = StringProp(lazy_gettext("ID"))
    client_name = StringProp(lazy_gettext("Application"))
    scope = StringProp(lazy_gettext("Scopes"))
    issued_at_datetime = DateTimeProp(lazy_gettext("Issued"))
    expires_at_datetime = DateTimeProp(lazy_gettext("Expires"))
    status = MethodProp("get_status_display_value", lazy_gettext("Status"))

    def get_status_display_value(self, object):
        if object.is_expired():  # pragma: no cover
            return gettext("Expired")

        if object.is_revoked():  # pragma: no cover
            return gettext("Revoked")

        return None
