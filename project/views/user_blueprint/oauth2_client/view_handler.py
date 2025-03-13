from flask import flash
from flask_babel import gettext

from project.models import OAuth2Client
from project.services.oauth2_client import complete_oauth2_client
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.child_view_handler import UserChildViewHandler
from project.views.user_blueprint.oauth2_client.displays import ListDisplay, ReadDisplay
from project.views.user_blueprint.oauth2_client.forms import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.views.utils import non_match_for_deletion


class OAuth2ClientViewHandler(UserChildViewHandler):
    model = OAuth2Client
    create_form_class = CreateOAuth2ClientForm
    update_form_class = UpdateOAuth2ClientForm
    delete_form_class = DeleteOAuth2ClientForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def complete_object(self, object, form):
        super().complete_object(object, form)
        complete_oauth2_client(object)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super().apply_objects_query_order(query, **kwargs).order_by(OAuth2Client.id)
        )

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.client_name):
            flash(gettext("Entered name does not match OAuth2 client name"), "danger")
            return False
        return True


handler = OAuth2ClientViewHandler()
handler.init_app(user_bp)
