from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import (
    DateProp,
    OrganizationAppPermissionListProp,
    StringProp,
)


class ReadDisplay(BaseDisplay):
    app = StringProp(lazy_gettext("App"), keypath="oauth2_client.client_name")
    permissions = OrganizationAppPermissionListProp(lazy_gettext("Permissions"))
    created_at = DateProp(lazy_gettext("Created at"))


class ListDisplay(BaseDisplay):
    app = StringProp(lazy_gettext("App"), keypath="oauth2_client.client_name")
    created_at = DateProp(lazy_gettext("Created at"))


class AcceptPermissionsDisplay(BaseDisplay):
    app = StringProp(lazy_gettext("App"), keypath="oauth2_client.client_name")
    permissions = OrganizationAppPermissionListProp(lazy_gettext("Current permissions"))
