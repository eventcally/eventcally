from flask import Blueprint, current_app

# The logged-in user's own area (profile, settings, API keys, OAuth2 clients and tokens,
# memberships and invitations). Session only (the parent answers 401 for anonymous
# visitors); the current user is implied, so no route carries a user id. Never imports the
# other BFF areas.
bff_user_bp = Blueprint("bff_user", __name__, url_prefix="/user")


def actor():
    return current_app.container.context.context_provider().current_actor


from project.presentation.bff.user import api_keys  # noqa: E402, F401
from project.presentation.bff.user import oauth2_clients  # noqa: E402, F401
from project.presentation.bff.user import oauth2_tokens  # noqa: E402, F401
from project.presentation.bff.user import organizations  # noqa: E402, F401
from project.presentation.bff.user import profile  # noqa: E402, F401
