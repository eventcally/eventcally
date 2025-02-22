from flask import abort
from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import func

from project.models import AdminUnitMemberInvitation
from project.utils import strings_are_equal_ignoring_case
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.child_view_handler import UserChildViewHandler
from project.views.user_blueprint.organization_member_invitation.displays import (
    ListDisplay,
)
from project.views.user_blueprint.organization_member_invitation.views import (
    NegotiateView,
)


class ViewHandler(UserChildViewHandler):
    model = AdminUnitMemberInvitation
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay

    def apply_base_filter(self, query, **kwargs):
        return query.filter(
            func.lower(self.model.email) == func.lower(current_user.email)
        )

    def check_object_access(self, object):
        if not strings_are_equal_ignoring_case(
            object.email, current_user.email
        ):  # pragma: no cover
            abort(401)
        return None

    def get_default_list_action(self, object):
        url = self._get_object_url("negotiate", object)
        return self._create_action(url, gettext("View"))

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        result = super()._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )
        self._add_view(
            "negotiate",
            f"/{single_url_folder}/<int:{id_query_arg_name}>/negotiate",
            NegotiateView,
            f"{single_endpoint_name}_negotiate",
            app,
        )

        return result


handler = ViewHandler()
handler.init_app(user_bp)
