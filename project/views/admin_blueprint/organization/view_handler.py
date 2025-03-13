from flask import url_for
from flask_babel import gettext
from sqlalchemy import func

from project.models.admin_unit import AdminUnit
from project.views.admin_blueprint import admin_bp
from project.views.admin_blueprint.child_view_handler import AdminChildViewHandler
from project.views.admin_blueprint.organization.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.views.admin_blueprint.organization.forms import DeleteForm, UpdateForm
from project.views.admin_blueprint.organization.views import DeleteView


class ViewHandler(AdminChildViewHandler):
    model = AdminUnit
    create_view_class = None
    read_view_class = None
    update_form_class = UpdateForm
    update_display_class = UpdateDisplay
    delete_view_class = DeleteView
    delete_form_class = DeleteForm
    list_display_class = ListDisplay

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(func.lower(AdminUnit.name))
        )

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_action = self._create_action(
            url_for(
                "organizations",
                path=object.id,
            ),
            gettext("View"),
        )
        if view_action:
            result.insert(0, view_action)

        manage_action = self._create_action(
            url_for(
                "manage_admin_unit",
                id=object.id,
            ),
            gettext("Manage"),
        )
        if manage_action:
            result.insert(0, manage_action)

        return result


handler = ViewHandler()
handler.init_app(admin_bp)
