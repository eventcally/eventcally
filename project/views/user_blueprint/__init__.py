from project.modular.base_blueprint import BaseBlueprint

user_bp = BaseBlueprint(
    "user",
    __name__,
    url_prefix="/user",
    template_folder="templates",
)

import project.views.user_blueprint.api_key.view_handler
import project.views.user_blueprint.oauth2_client.view_handler
import project.views.user_blueprint.oauth2_token.view_handler
import project.views.user_blueprint.organization_invitation.view_handler
import project.views.user_blueprint.organization_member.view_handler
import project.views.user_blueprint.organization_member_invitation.view_handler
import project.views.user_blueprint.user.view_handler
from project import app

app.register_blueprint(user_bp)
