from flask import Blueprint

# The pages of the logged-in user area. Every route is a shell for the `user` Vue entry
# (see `shells.py`); the data and the writes go through `/bff/user`.
user_bp = Blueprint("user", __name__, url_prefix="/user")

import project.presentation.web.views.user_blueprint.shells  # noqa: E402, F401
