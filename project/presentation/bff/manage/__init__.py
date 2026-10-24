from flask import Blueprint

# Logged-in pages outside the admin. Session only (the parent answers 401 for anonymous
# visitors); each route authorizes its own use case.
bff_manage_bp = Blueprint("bff_manage", __name__, url_prefix="/manage")

from project.presentation.bff.manage import custom_widgets  # noqa: E402, F401
from project.presentation.bff.manage import event_places  # noqa: E402, F401
from project.presentation.bff.manage import event_references  # noqa: E402, F401
from project.presentation.bff.manage import events  # noqa: E402, F401
from project.presentation.bff.manage import organization_export  # noqa: E402, F401
from project.presentation.bff.manage import organization_settings  # noqa: E402, F401
from project.presentation.bff.manage import organizations  # noqa: E402, F401
from project.presentation.bff.manage import places  # noqa: E402, F401
from project.presentation.bff.manage import planning  # noqa: E402, F401
from project.presentation.bff.manage import request_reviews  # noqa: E402, F401
