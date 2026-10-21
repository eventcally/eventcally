from flask import Blueprint

from project.domain.errors import UnauthorizedError
from project.presentation.shared.access import is_platform_admin

bff_admin_bp = Blueprint("bff_admin", __name__, url_prefix="/admin")


@bff_admin_bp.before_request
def _require_platform_admin():
    # Runs after the parent's 401 hook, so anonymous users never get here. Some routes
    # (the mail config) have no query that could authorize them.
    if not is_platform_admin():
        raise UnauthorizedError()


from project.presentation.bff.admin import mail  # noqa: E402, F401
from project.presentation.bff.admin import organizations  # noqa: E402, F401
from project.presentation.bff.admin import settings  # noqa: E402, F401
from project.presentation.bff.admin import users  # noqa: E402, F401
