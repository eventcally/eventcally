from flask_babel import gettext
from flask_login import current_user
from flask_security import auth_required

from project.application.queries import (
    GetUserOAuth2TokenQuery,
    ListUserOAuth2TokensQuery,
)
from project.presentation.web.views.user_blueprint import user_bp
from project.presentation.web.views.user_blueprint.child_view_handler import (
    UserChildViewHandler,
)
from project.presentation.web.views.user_blueprint.oauth2_token.displays import (
    ListDisplay,
)
from project.presentation.web.views.user_blueprint.oauth2_token.views import RevokeView


class OAuth2TokenViewHandler(UserChildViewHandler):
    decorators = [auth_required()]
    model_name = "oauth2_token"
    model_name_plural = "oauth2_tokens"
    display_name = "OAuth2 token"
    display_name_plural = "OAuth2 tokens"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        super()._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )

        self._add_view(
            "revoke",
            f"/{single_url_folder}/<int:{id_query_arg_name}>/revoke",
            RevokeView,
            f"{single_endpoint_name}_revoke",
            app,
        )

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        if not object.is_revoked():
            kwargs = dict()
            kwargs.setdefault(self.get_id_query_arg_name(), object.id)
            revoke_action = self._create_action(
                self.get_endpoint_url("revoke", **kwargs), gettext("Revoke")
            )
            if revoke_action:
                result.append(revoke_action)

        return result

    def create_list_query(self, form, page_request, **kwargs):
        return ListUserOAuth2TokensQuery(user_id=current_user.id, page=page_request)

    def create_get_query(self, object_id):
        return GetUserOAuth2TokenQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `OAuth2Token.__str__`.
        return f"{self.get_model_display_name()} {object.id} ({object.client_name})"


handler = OAuth2TokenViewHandler()
handler.init_app(user_bp)
