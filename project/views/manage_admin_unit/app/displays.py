from flask import url_for
from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import (
    ListProp,
    OrganizationAppPermissionListProp,
    StringProp,
    URLProp,
)


class ReadDisplay(BaseDisplay):
    client_id = StringProp(lazy_gettext("Client ID"))
    client_secret = StringProp(lazy_gettext("Client secret"))
    grant_types = ListProp(lazy_gettext("Grant types"))
    redirect_uris = ListProp(lazy_gettext("Redirect URIs"))
    response_types = ListProp(lazy_gettext("Response types"))
    scope = StringProp(lazy_gettext("Scope"))
    token_endpoint_auth_method = ListProp(lazy_gettext("Token endpoint auth method"))
    app_permissions = OrganizationAppPermissionListProp(lazy_gettext("Permissions"))
    homepage_url = URLProp(lazy_gettext("Homepage"))
    setup_url = URLProp(lazy_gettext("Setup URL"))
    webhook_url = URLProp(lazy_gettext("Webhook URL"), keypath="webhook.url")
    description = StringProp(lazy_gettext("Description"))
    app_keys = StringProp(
        lazy_gettext("App keys"),
        method_name="get_app_keys",
        link_method_name="get_app_keys_link",
    )
    webhook_deliveries = StringProp(
        lazy_gettext("Webhook deliveries"),
        method_name="get_webhook_deliveries",
        link_method_name="get_webhook_deliveries_link",
    )

    def get_app_keys(self, object):
        return lazy_gettext("App keys")

    def get_app_keys_link(self, object):
        return url_for(".app.app_keys", app_id=object.id)

    def get_webhook_deliveries(self, object):
        return lazy_gettext("Webhook deliveries")

    def get_webhook_deliveries_link(self, object):
        return url_for(".app.webhook_deliveries", app_id=object.id)


class ListDisplay(BaseDisplay):
    client_name = StringProp(lazy_gettext("Client Name"))
