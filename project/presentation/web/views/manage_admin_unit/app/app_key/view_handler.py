from flask import g

from project.application.queries import GetAppKeyQuery, ListAppKeysQuery
from project.presentation.web.views.manage_admin_unit.app import app_bp
from project.presentation.web.views.manage_admin_unit.app.app_key.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.presentation.web.views.manage_admin_unit.app.app_key.forms import (
    DeleteForm,
)
from project.presentation.web.views.manage_admin_unit.app.app_key.views import (
    CreateView,
    DeleteView,
    ReadView,
)
from project.presentation.web.views.manage_admin_unit.app.child_view_handler import (
    AppChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.app.view_handler import (
    handler as app_view_handler,
)


class AppKeyViewHandler(AppChildViewHandler):
    model_name = "app_key"
    model_name_plural = "app_keys"
    display_name = "App key"
    display_name_plural = "App keys"
    create_view_class = CreateView
    update_view_class = None
    delete_form_class = DeleteForm
    delete_view_class = DeleteView
    list_display_class = ListDisplay
    read_view_class = ReadView
    read_display_class = ReadDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListAppKeysQuery(app_id=g.current_app.id, page=page_request)

    def create_get_query(self, object_id):
        return GetAppKeyQuery(id=object_id)

    def get_object_by_id(self, object_id):
        # A key of another app is not found (not unauthorized), as before.
        app_key = super().get_object_by_id(object_id)
        return (
            app_key
            if app_key and app_key.oauth2_client_id == g.current_app.id
            else None
        )

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = AppKeyViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
