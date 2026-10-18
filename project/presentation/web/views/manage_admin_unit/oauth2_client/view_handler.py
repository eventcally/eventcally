from flask_babel import gettext

from project.application.queries import (
    GetOAuth2ClientQuery,
    ListOrganizationOAuth2ClientsQuery,
)
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.oauth2_client.views import (
    CreateView,
)
from project.presentation.web.views.user_blueprint.oauth2_client.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.presentation.web.views.user_blueprint.oauth2_client.forms import (
    CreateOAuth2ClientForm,
    DeleteOAuth2ClientForm,
    UpdateOAuth2ClientForm,
)
from project.presentation.web.views.user_blueprint.oauth2_client.views import (
    DeleteView,
    UpdateView,
)
from project.presentation.web.views.utils import flash_non_match_for_deletion


class OAuth2ClientViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "oauth2_client"
    model_name_plural = "oauth2_clients"
    display_name = "OAuth2 client"
    display_name_plural = "OAuth2 clients"
    create_view_class = CreateView
    create_form_class = CreateOAuth2ClientForm
    update_view_class = UpdateView
    update_form_class = UpdateOAuth2ClientForm
    delete_view_class = DeleteView
    delete_form_class = DeleteOAuth2ClientForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListOrganizationOAuth2ClientsQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetOAuth2ClientQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `OAuth2Client.__str__`.
        return object.client_name or f"{self.get_model_display_name()} {object.id}"

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.client_name,
            gettext("Entered name does not match OAuth2 client name"),
        )


handler = OAuth2ClientViewHandler()
handler.init_app(manage_admin_unit_bp)
