from project.models import AdminUnit
from project.views.manage_blueprint import manage_bp
from project.views.manage_blueprint.child_view_handler import ManageChildViewHandler
from project.views.manage_blueprint.organization.views import CreateView


class ViewHandler(ManageChildViewHandler):
    model = AdminUnit
    create_view_class = CreateView
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = None


handler = ViewHandler()
handler.init_app(manage_bp)
