from flask import flash, url_for
from flask_babel import gettext, lazy_gettext
from flask_security import auth_required, current_user

from project import app
from project.access import owner_access_or_401
from project.forms.oauth2_client import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.models import OAuth2Client
from project.services.oauth2_client import complete_oauth2_client
from project.views.base_display import BaseDisplay
from project.views.base_props import ListProp, StringProp
from project.views.base_view_handler import BaseViewHandler
from project.views.utils import non_match_for_deletion


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


class OAuth2ClientViewHandler(BaseViewHandler):
    decorators = [auth_required()]
    model = OAuth2Client
    create_form_class = CreateOAuth2ClientForm
    update_form_class = UpdateOAuth2ClientForm
    delete_form_class = DeleteOAuth2ClientForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()
        result.append(self._create_breadcrumb(url_for("profile"), gettext("Profile")))
        return result

    def complete_object(self, object):
        object.user_id = current_user.id
        complete_oauth2_client(object)

    def check_object_access(self, object):
        return owner_access_or_401(object.user_id)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(OAuth2Client.user_id == current_user.id)

    def apply_objects_query_order(self, query, **kwargs):
        return query.order_by(OAuth2Client.id)

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.client_name):
            flash(gettext("Entered name does not match OAuth2 client name"), "danger")
            return False
        return True


handler = OAuth2ClientViewHandler()
handler.init_app(app)
