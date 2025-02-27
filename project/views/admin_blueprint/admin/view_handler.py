from flask_security import roles_required

from project.modular.base_view_handler import BaseViewHandler
from project.views.admin_blueprint import admin_bp
from project.views.admin_blueprint.admin.views import AdminView


class ViewHandler(BaseViewHandler):
    decorators = [roles_required("admin")]
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = None

    def get_template_folder(self):
        return f"{self.generic_prefix}admin"

    def add_views(self, app):
        self._add_view(
            "root",
            "",
            AdminView,
            "admin",
            app,
        )


handler = ViewHandler()
handler.init_app(admin_bp)
