from flask_babel import lazy_gettext
from flask_login import current_user

from project.application.queries import ApiKeySort, GetApiKeyQuery, ListUserApiKeysQuery
from project.presentation.web.modular.sort_definition import (
    KeySortDefinition,
    sort_key_or_none,
)
from project.presentation.web.views.user_blueprint import user_bp
from project.presentation.web.views.user_blueprint.api_key.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.presentation.web.views.user_blueprint.api_key.forms import (
    CreateForm,
    DeleteForm,
    UpdateForm,
)
from project.presentation.web.views.user_blueprint.api_key.views import (
    CreateView,
    DeleteView,
    UpdateView,
)
from project.presentation.web.views.user_blueprint.child_view_handler import (
    UserChildViewHandler,
)


class ApiKeyViewHandler(UserChildViewHandler):
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
        return ListUserApiKeysQuery(
            user_id=current_user.id,
            sort=sort_key_or_none(ApiKeySort, form.sort.data),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetApiKeyQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = ApiKeyViewHandler()
handler.init_app(user_bp)
