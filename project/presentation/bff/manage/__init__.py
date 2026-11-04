from flask import Blueprint

# Logged-in pages outside the admin. Session only (the parent answers 401 for anonymous
# visitors); each route authorizes its own use case.
bff_manage_bp = Blueprint("bff_manage", __name__, url_prefix="/manage")

from project.presentation.bff.manage import api_keys  # noqa: E402, F401
from project.presentation.bff.manage import custom_widgets  # noqa: E402, F401
from project.presentation.bff.manage import event_forms  # noqa: E402, F401
from project.presentation.bff.manage import event_organizers  # noqa: E402, F401
from project.presentation.bff.manage import event_places  # noqa: E402, F401
from project.presentation.bff.manage import event_references  # noqa: E402, F401
from project.presentation.bff.manage import events  # noqa: E402, F401
from project.presentation.bff.manage import member_invitations  # noqa: E402, F401
from project.presentation.bff.manage import members  # noqa: E402, F401
from project.presentation.bff.manage import oauth2_clients  # noqa: E402, F401
from project.presentation.bff.manage import organization_deletion  # noqa: E402, F401
from project.presentation.bff.manage import organization_export  # noqa: E402, F401
from project.presentation.bff.manage import organization_settings  # noqa: E402, F401
from project.presentation.bff.manage import organizations  # noqa: E402, F401
from project.presentation.bff.manage import outgoing_relations  # noqa: E402, F401
from project.presentation.bff.manage import places  # noqa: E402, F401
from project.presentation.bff.manage import planning  # noqa: E402, F401
from project.presentation.bff.manage import reference_requests  # noqa: E402, F401
from project.presentation.bff.manage import request_reviews  # noqa: E402, F401
from project.presentation.bff.manage import verification_requests  # noqa: E402, F401
from project.presentation.bff.manage import widget_settings  # noqa: E402, F401
from project.presentation.bff.manage import (  # noqa: E402, F401
    organization_invitations,
    outgoing_reference_requests,
)
