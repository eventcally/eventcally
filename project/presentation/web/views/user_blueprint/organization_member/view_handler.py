from flask_babel import lazy_gettext
from flask_login import current_user

from project.application.queries import (
    GetUserOrganizationMembershipQuery,
    ListUserOrganizationMembershipsQuery,
)
from project.presentation.web.views.user_blueprint import user_bp
from project.presentation.web.views.user_blueprint.child_view_handler import (
    UserChildViewHandler,
)
from project.presentation.web.views.user_blueprint.organization_member.displays import (
    ListDisplay,
)
from project.presentation.web.views.user_blueprint.organization_member.views import (
    DeleteView,
)


class ViewHandler(UserChildViewHandler):
    model_name = "organization_member"
    model_name_plural = "organization_members"
    display_name = "Organization member"
    display_name_plural = "Organization members"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = DeleteView
    list_display_class = ListDisplay

    def get_model_display_name_plural(self):
        return lazy_gettext("Organizations")

    def create_list_query(self, form, page_request, **kwargs):
        return ListUserOrganizationMembershipsQuery(
            user_id=current_user.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetUserOrganizationMembershipQuery(id=object_id)


handler = ViewHandler()
handler.init_app(user_bp)
