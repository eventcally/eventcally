from flask_babel import lazy_gettext
from sqlalchemy import func

from project.models import ApiKey
from project.modular.sort_definition import SortDefinition
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.user_blueprint.api_key.displays import ListDisplay, ReadDisplay
from project.views.user_blueprint.api_key.forms import (
    CreateForm,
    DeleteForm,
    UpdateForm,
)
from project.views.user_blueprint.api_key.views import CreateView


class ApiKeyViewHandler(ManageAdminUnitChildViewHandler):
    model = ApiKey
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
handler.init_app(manage_admin_unit_bp)
