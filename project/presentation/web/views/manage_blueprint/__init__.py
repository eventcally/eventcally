from flask import Blueprint

manage_bp = Blueprint("manage", __name__, url_prefix="/manage")

import project.presentation.web.views.manage_blueprint.views  # noqa: E402, F401
