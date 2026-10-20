from flask import Blueprint

bff_admin_bp = Blueprint("bff_admin", __name__, url_prefix="/admin")

from project.presentation.bff.admin import settings  # noqa: E402, F401
from project.presentation.bff.admin import users  # noqa: E402, F401
