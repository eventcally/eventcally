from flask_babel import lazy_gettext

from project.application.queries import (
    ApiKeySort,
    GetApiKeyQuery,
    ListOrganizationApiKeysQuery,
)
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.api_key.views import CreateView
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.modular.sort_definition import KeySortDefinition, sort_key_or_none
from project.views.user_blueprint.api_key.displays import ListDisplay, ReadDisplay
from project.views.user_blueprint.api_key.forms import (
    CreateForm,
    DeleteForm,
    UpdateForm,
)
from project.views.user_blueprint.api_key.views import DeleteView, UpdateView
from project.views.utils import current_admin_unit


class ApiKeyViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "api_key"
    model_name_plural = "api_keys"
    display_name = "API key"
    display_name_plural = "API keys"
    create_view_class = CreateView
    create_form_class = CreateForm
    update_view_class = UpdateView
    update_form_class = UpdateForm
    delete_view_class = DeleteView
    delete_form_class = DeleteForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay
    list_sort_definitions = [
        KeySortDefinition(ApiKeySort.name.value, label=lazy_gettext("Name")),
        KeySortDefinition(
            ApiKeySort.created_at_desc.value,
            label=lazy_gettext("Last created first"),
        ),
    ]

    def create_list_query(self, form, page_request, **kwargs):
        return ListOrganizationApiKeysQuery(
            admin_unit_id=current_admin_unit.id,
            sort=sort_key_or_none(ApiKeySort, form.sort.data),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetApiKeyQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = ApiKeyViewHandler()
handler.init_app(manage_admin_unit_bp)
