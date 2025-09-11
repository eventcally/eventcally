from project.models import AppKey
from project.views.manage_admin_unit.app import app_bp
from project.views.manage_admin_unit.app.app_key.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.app.app_key.forms import DeleteForm
from project.views.manage_admin_unit.app.app_key.views import CreateView, ReadView
from project.views.manage_admin_unit.app.child_view_handler import AppChildViewHandler
from project.views.manage_admin_unit.app.view_handler import handler as app_view_handler


class AppKeyViewHandler(AppChildViewHandler):
    model = AppKey
    create_view_class = CreateView
    update_view_class = None
    delete_form_class = DeleteForm
    list_display_class = ListDisplay
    read_view_class = ReadView
    read_display_class = ReadDisplay


handler = AppKeyViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
