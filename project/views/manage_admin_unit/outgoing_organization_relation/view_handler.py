from flask_babel import gettext, lazy_gettext

from project.application.queries import (
    GetOutgoingOrganizationRelationQuery,
    ListOutgoingOrganizationRelationsQuery,
    OrganizationRelationSort,
)
from project.modular.base_form import BaseDeleteForm
from project.modular.filters import KeyBooleanFilter
from project.modular.search_definition import KeySearchDefinition
from project.modular.sort_definition import KeySortDefinition, sort_key_or_none
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
    DeleteView,
    ListView,
    UpdateView,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "organization_relation"
    model_name_plural = "organization_relations"
    display_name = "Organization relation"
    display_name_plural = "Organization relations"
    admin_unit_id_attribute_name = "source_admin_unit_id"
    create_form_class = CreateForm
    create_view_class = CreateView
    read_view_class = None
    update_form_class = UpdateForm
    update_view_class = UpdateView
    update_display_class = UpdateDisplay
    delete_form_class = BaseDeleteForm
    delete_view_class = DeleteView
    list_display_class = ListDisplay
    list_view_class = ListView
    list_filters = [
        KeyBooleanFilter("verify", label=lazy_gettext("Verify other organization")),
        KeyBooleanFilter(
            "auto_verify_event_reference_requests",
            label=lazy_gettext("Verify reference requests automatically"),
        ),
    ]
    list_search_definitions = [KeySearchDefinition("name")]
    list_sort_definitions = [
        KeySortDefinition(
            OrganizationRelationSort.name.value, label=lazy_gettext("Name")
        ),
        KeySortDefinition(
            OrganizationRelationSort.last_modified_at_desc.value,
            label=lazy_gettext("Last modified first"),
        ),
    ]
    generic_prefix = "outgoing_"

    def get_model_display_name(self):
        return lazy_gettext("Outgoing organization relation")

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing organization relations")

    def create_list_query(self, form, page_request, **kwargs):
        # The list view removes the `verify` field when the organization cannot
        # verify others; the filter is then not applied, as before.
        verify_field = form["verify"] if "verify" in form else None

        return ListOutgoingOrganizationRelationsQuery(
            admin_unit_id=current_admin_unit.id,
            keyword=form.keyword.data or None,
            verify=_bool_or_none(verify_field.data if verify_field else None),
            auto_verify_event_reference_requests=_bool_or_none(
                form.auto_verify_event_reference_requests.data
            ),
            sort=sort_key_or_none(OrganizationRelationSort, form.sort.data),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetOutgoingOrganizationRelationQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__` (the model's display name).
        return f"{gettext(self.display_name)} {object.id}"


def _bool_or_none(value):
    return {"1": True, "0": False}.get(value)


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
