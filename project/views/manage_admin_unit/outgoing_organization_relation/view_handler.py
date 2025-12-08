from typing import Annotated

from dependency_injector.wiring import Provide
from flask_babel import lazy_gettext
from sqlalchemy import func

from project.models import AdminUnitRelation
from project.models.admin_unit import AdminUnit
from project.modular.base_form import BaseDeleteForm
from project.modular.filters import BooleanFilter
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.services.organization_relation_service import OrganizationRelationService
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.outgoing_organization_relation.displays import (
    ListDisplay,
    UpdateDisplay,
)
from project.views.manage_admin_unit.outgoing_organization_relation.forms import (
    CreateForm,
    UpdateForm,
)
from project.views.manage_admin_unit.outgoing_organization_relation.views import (
    CreateView,
    ListView,
    UpdateView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = AdminUnitRelation
    object_service: Annotated[
        OrganizationRelationService, Provide["services.organization_relation_service"]
    ]
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_form_class = CreateForm
    create_view_class = CreateView
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    list_display_class = ListDisplay
    list_view_class = ListView
    list_filters = [
        BooleanFilter(
            AdminUnitRelation.verify, label=lazy_gettext("Verify other organization")
        ),
        BooleanFilter(
            AdminUnitRelation.auto_verify_event_reference_requests,
            label=lazy_gettext("Verify reference requests automatically"),
        ),
    ]
    list_search_definitions = [SearchDefinition(AdminUnit.name)]
    list_sort_definitions = [
        SortDefinition(AdminUnit.name, func=func.lower, label=lazy_gettext("Name")),
        SortDefinition(
            AdminUnit.last_modified_at,
            desc=True,
            label=lazy_gettext("Last modified first"),
        ),
    ]
    generic_prefix = "outgoing_"

    def get_model_display_name(self):
        return lazy_gettext("Outgoing organization relation")

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing organization relations")

    def get_objects_base_query_from_kwargs(self, **kwargs):
        return (
            super()
            .get_objects_base_query_from_kwargs(**kwargs)
            .join(AdminUnit, AdminUnitRelation.target_admin_unit_id == AdminUnit.id)
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
