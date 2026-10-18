from flask import g

from project.presentation.web.modular.base_blueprint import BaseBlueprint

manage_bp = BaseBlueprint(
    "manage",
    __name__,
    url_prefix="/manage",
    template_folder="templates",
    static_folder="static",
)

import project.presentation.web.views.manage_blueprint.organization.view_handler
