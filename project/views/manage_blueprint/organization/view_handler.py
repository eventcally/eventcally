from project.views.manage_blueprint import manage_bp
from project.views.manage_blueprint.child_view_handler import ManageChildViewHandler
from project.views.manage_blueprint.organization.views import CreateView


class ViewHandler(ManageChildViewHandler):
    model_name = "organization"
    model_name_plural = "organizations"
    display_name = "Organization"
    display_name_plural = "Organizations"
    create_view_class = CreateView
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = None


handler = ViewHandler()
handler.init_app(manage_bp)
