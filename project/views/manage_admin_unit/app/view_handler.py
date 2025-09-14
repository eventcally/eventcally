from flask_babel import gettext

from project.models import OAuth2Client
from project.services.oauth2_client import complete_oauth2_client
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.app.displays import ListDisplay, ReadDisplay
from project.views.manage_admin_unit.app.forms import (
    CreateAppForm,
    DeleteAppForm,
    UpdateAppForm,
)
from project.views.manage_admin_unit.app.views import CreateView, UpdateView
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.utils import flash_non_match_for_deletion


class AppViewHandler(ManageAdminUnitChildViewHandler):
    model = OAuth2Client
    create_form_class = CreateAppForm
    create_view_class = CreateView
    update_form_class = UpdateAppForm
    update_view_class = UpdateView
    delete_form_class = DeleteAppForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def get_model_name(self):
        return "app"

    def get_model_name_plural(self):
        return "apps"

    def get_model_display_name(self):
        return gettext("App")

    def get_model_display_name_plural(self):
        return gettext("Apps")

    def apply_base_filter(self, query, **kwargs):
        return (
            super()
            .apply_base_filter(query, **kwargs)
            .filter(OAuth2Client.app_permissions.isnot(None))
        )

    def complete_object(self, object, form):
        super().complete_object(object, form)
        complete_oauth2_client(object)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super().apply_objects_query_order(query, **kwargs).order_by(OAuth2Client.id)
        )

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.client_name,
            gettext("Entered name does not match app client name"),
        )


handler = AppViewHandler()
handler.init_app(manage_admin_unit_bp)
