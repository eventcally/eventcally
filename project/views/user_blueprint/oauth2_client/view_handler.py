from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import gettext

from project.models import OAuth2Client
from project.services.oauth2_client_service import OAuth2ClientService
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.child_view_handler import UserChildViewHandler
from project.views.user_blueprint.oauth2_client.displays import ListDisplay, ReadDisplay
from project.views.user_blueprint.oauth2_client.forms import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.views.user_blueprint.oauth2_client.views import (
    CreateView,
    DeleteView,
    UpdateView,
)
from project.views.utils import flash_non_match_for_deletion


class OAuth2ClientViewHandler(UserChildViewHandler):
    model = OAuth2Client
    object_service: Annotated[
        OAuth2ClientService, Provide["services.oauth2_client_service"]
    ]
    create_view_class = CreateView
    create_form_class = CreateOAuth2ClientForm
    update_view_class = UpdateView
    update_form_class = UpdateOAuth2ClientForm
    delete_view_class = DeleteView
    delete_form_class = DeleteOAuth2ClientForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super().apply_objects_query_order(query, **kwargs).order_by(OAuth2Client.id)
        )

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.client_name,
            gettext("Entered name does not match OAuth2 client name"),
        )


handler = OAuth2ClientViewHandler()
handler.init_app(user_bp)
