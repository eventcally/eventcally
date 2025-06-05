from flask import g

from project.modular.base_blueprint import BaseBlueprint

manage_bp = BaseBlueprint(
    "manage",
    __name__,
    url_prefix="/manage",
    template_folder="templates",
    static_folder="static",
)

import project.views.manage_blueprint.organization.view_handler
from project import app

app.register_blueprint(manage_bp)
