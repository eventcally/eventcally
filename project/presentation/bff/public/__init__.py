from flask import Blueprint

# Anonymous endpoints for the public Vue pages. The parent blueprint lets this one
# through its session check (CSRF still applies to unsafe methods); writes are rate limited.
bff_public_bp = Blueprint("bff_public", __name__, url_prefix="/public")

from project.presentation.bff.public import events  # noqa: E402, F401
from project.presentation.bff.public import organizations  # noqa: E402, F401
from project.presentation.bff.public import organizers  # noqa: E402, F401
from project.presentation.bff.public import widget  # noqa: E402, F401
