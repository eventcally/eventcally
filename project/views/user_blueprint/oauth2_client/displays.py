from flask_babel import lazy_gettext

from project.modular.base_display import BaseDisplay
from project.modular.base_props import ListProp, StringProp


class ReadDisplay(BaseDisplay):
    client_id = StringProp(lazy_gettext("Client ID"))
    client_secret = StringProp(lazy_gettext("Client secret"))
    client_uri = StringProp(lazy_gettext("Client URI"))
    grant_types = ListProp(lazy_gettext("Grant types"))
    redirect_uris = ListProp(lazy_gettext("Redirect URIs"))
    response_types = ListProp(lazy_gettext("Response types"))
    scope = StringProp(lazy_gettext("Scope"))
    token_endpoint_auth_method = ListProp(lazy_gettext("Token endpoint auth method"))


class ListDisplay(BaseDisplay):
    client_name = StringProp(lazy_gettext("Client Name"))
