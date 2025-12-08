from typing import Annotated

from dependency_injector.wiring import Provide
from flask import g

from project.models import AppKey
from project.services.app_service import AppService
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
    object_service: Annotated[AppService, Provide["services.app_service"]]
    create_view_class = CreateView
    update_view_class = None
    delete_form_class = DeleteForm
    list_display_class = ListDisplay
    read_view_class = ReadView
    read_display_class = ReadDisplay

    def get_object_by_id(self, object_id):
        return self.object_service.get_app_key_by_id(g.current_app, object_id)

    def insert_object(self, object):
        self.object_service.insert_app_key(g.current_app, object)

    def delete_object(self, object):
        self.object_service.delete_app_key(g.current_app, object)


handler = AppKeyViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
