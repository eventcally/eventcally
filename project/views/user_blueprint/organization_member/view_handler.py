from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import lazy_gettext

from project.models import AdminUnitMember
from project.services.organization_member_service import OrganizationMemberService
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.child_view_handler import UserChildViewHandler
from project.views.user_blueprint.organization_member.displays import ListDisplay
from project.views.user_blueprint.organization_member.views import DeleteView


class ViewHandler(UserChildViewHandler):
    model = AdminUnitMember
    object_service: Annotated[
        OrganizationMemberService, Provide["services.organization_member_service"]
    ]
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = DeleteView
    list_display_class = ListDisplay

    def get_model_display_name_plural(self):
        return lazy_gettext("Organizations")


handler = ViewHandler()
handler.init_app(user_bp)
