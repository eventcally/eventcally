from flask_babel import gettext

from project.application.queries import GetAppQuery, ListAppsQuery
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.app.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.presentation.web.views.manage_admin_unit.app.forms import (
    CreateAppForm,
    DeleteAppForm,
    UpdateAppForm,
)
from project.presentation.web.views.manage_admin_unit.app.views import (
    CreateView,
    DeleteView,
    UpdateView,
)
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.utils import flash_non_match_for_deletion


class AppViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "app"
    model_name_plural = "apps"
    display_name = "App"
    display_name_plural = "Apps"
    create_form_class = CreateAppForm
    create_view_class = CreateView
    update_form_class = UpdateAppForm
    update_view_class = UpdateView
    delete_form_class = DeleteAppForm
    delete_view_class = DeleteView
    read_display_class = ReadDisplay
    list_display_class = ListDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListAppsQuery(admin_unit_id=current_admin_unit.id, page=page_request)

    def create_get_query(self, object_id):
        return GetAppQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `OAuth2Client.__str__`.
        return object.client_name or f"{gettext('OAuth2 client')} {object.id}"

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.client_name,
            gettext("Entered name does not match app client name"),
        )


handler = AppViewHandler()
handler.init_app(manage_admin_unit_bp)
