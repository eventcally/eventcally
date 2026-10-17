from flask import url_for
from flask_babel import gettext

from project.application.commands import DeleteOrganizationCommand
from project.application.queries import (
    GetOrganizationForAdminQuery,
    ListOrganizationsForAdminQuery,
)
from project.presentation.web.modular.search_definition import KeySearchDefinition
from project.presentation.web.views.admin_blueprint import admin_bp
from project.presentation.web.views.admin_blueprint.child_view_handler import (
    AdminChildViewHandler,
)
from project.presentation.web.views.admin_blueprint.organization.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.presentation.web.views.admin_blueprint.organization.forms import (
    DeleteForm,
    UpdateForm,
)
from project.presentation.web.views.admin_blueprint.organization.views import (
    DeleteView,
    UpdateView,
)


class ViewHandler(AdminChildViewHandler):
    model_name = "organization"
    model_name_plural = "organizations"
    display_name = "Organization"
    display_name_plural = "Organizations"
    create_view_class = None
    read_view_class = None
    update_view_class = UpdateView
    update_form_class = UpdateForm
    update_display_class = UpdateDisplay
    delete_view_class = DeleteView
    delete_form_class = DeleteForm
    list_display_class = ListDisplay
    list_search_definitions = [KeySearchDefinition("name")]

    def delete_object(self, object):
        cmd = DeleteOrganizationCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

    def create_list_query(self, form, page_request, **kwargs):
        return ListOrganizationsForAdminQuery(
            keyword=form.keyword.data or None, page=page_request
        )

    def create_get_query(self, object_id):
        return GetOrganizationForAdminQuery(id=object_id)

    def get_object_title(self, object):
        return object.name

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_action = self._create_action(
            url_for(
                "main.organizations",
                path=object.id,
            ),
            gettext("View"),
        )
        if view_action:
            result.insert(0, view_action)

        manage_action = self._create_action(
            url_for(
                "main.manage_admin_unit",
                id=object.id,
            ),
            gettext("Manage"),
        )
        if manage_action:
            result.insert(0, manage_action)

        return result


handler = ViewHandler()
handler.init_app(admin_bp)
