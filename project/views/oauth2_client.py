from flask import flash, url_for
from flask_babel import gettext
from flask_security import auth_required, current_user

from project import app
from project.access import owner_access_or_401
from project.forms.oauth2_client import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    ReadOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.models import OAuth2Client
from project.services.oauth2_client import complete_oauth2_client
from project.views.base_view_handler import BaseViewHandler
from project.views.utils import non_match_for_deletion


class OAuth2ClientViewHandler(BaseViewHandler):
    decorators = [auth_required()]
    model = OAuth2Client
    create_form_class = CreateOAuth2ClientForm
    update_form_class = UpdateOAuth2ClientForm
    delete_form_class = DeleteOAuth2ClientForm
    read_form_class = ReadOAuth2ClientForm

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()
        result.append(
            {
                "url": url_for("profile"),
                "title": gettext("Profile"),
            }
        )
        return result

    def complete_object(self, object):
        object.user_id = current_user.id
        complete_oauth2_client(object)

    def check_object_access(self, object):
        owner_access_or_401(object.user_id)

    def apply_base_filter(self, query, **kwargs):
        return query.filter(OAuth2Client.user_id == current_user.id).order_by(
            OAuth2Client.id
        )

    def apply_objects_query_order(self, query, **kwargs):
        return query.order_by(OAuth2Client.id)

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.client_name):
            flash(gettext("Entered name does not match OAuth2 client name"), "danger")
            return False
        return True


handler = OAuth2ClientViewHandler()
handler.init_app(app)
