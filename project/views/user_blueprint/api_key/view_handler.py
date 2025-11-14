from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import lazy_gettext
from sqlalchemy import func

from project.models import ApiKey
from project.modular.sort_definition import SortDefinition
from project.services.api_key_service import ApiKeyService
from project.views.user_blueprint import user_bp
from project.views.user_blueprint.api_key.displays import ListDisplay, ReadDisplay
from project.views.user_blueprint.api_key.forms import (
    CreateForm,
    DeleteForm,
    UpdateForm,
)
from project.views.user_blueprint.api_key.views import CreateView
from project.views.user_blueprint.child_view_handler import UserChildViewHandler


class ApiKeyViewHandler(UserChildViewHandler):
    model = ApiKey
    object_service: Annotated[ApiKeyService, Provide["services.api_key_service"]]
    create_view_class = CreateView
    create_form_class = CreateForm
    update_form_class = UpdateForm
    delete_form_class = DeleteForm
    read_display_class = ReadDisplay
    list_display_class = ListDisplay
    list_sort_definitions = [
        SortDefinition(ApiKey.name, func=func.lower, label=lazy_gettext("Name")),
        SortDefinition(
            ApiKey.created_at,
            desc=True,
            label=lazy_gettext("Last created first"),
        ),
    ]


handler = ApiKeyViewHandler()
handler.init_app(user_bp)
