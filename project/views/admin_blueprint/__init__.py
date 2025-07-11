from project.modular.base_blueprint import BaseBlueprint

admin_bp = BaseBlueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)

import project.views.admin_blueprint.admin.view_handler
import project.views.admin_blueprint.organization.view_handler
from project import app

app.register_blueprint(admin_bp)
