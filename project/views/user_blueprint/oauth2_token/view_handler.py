from flask_babel import gettext
from flask_security import auth_required

from project.models import OAuth2Token
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.child_view_handler import UserChildViewHandler
from project.views.user_blueprint.oauth2_token.displays import ListDisplay
from project.views.user_blueprint.oauth2_token.views import RevokeView


class OAuth2TokenViewHandler(UserChildViewHandler):
    decorators = [auth_required()]
    model = OAuth2Token
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

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(OAuth2Token.issued_at.desc())
        )


handler = OAuth2TokenViewHandler()
handler.init_app(user_bp)
