from project.presentation.web.modular.base_blueprint import BaseBlueprint

admin_bp = BaseBlueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)

import project.presentation.web.views.admin_blueprint.admin.view_handler
import project.presentation.web.views.admin_blueprint.organization.view_handler
