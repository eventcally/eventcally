from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.application.queries import (
    GetIncomingEventReferenceQuery,
    ListIncomingEventReferencesQuery,
)
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.incoming_event_reference.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.incoming_event_reference.forms import (
    DeleteEventReferenceForm,
    UpdateEventReferenceForm,
)
from project.views.manage_admin_unit.incoming_event_reference.views import (
    DeleteView,
    ListView,
    UpdateView,
)
from project.views.utils import current_admin_unit


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "event_reference"
    model_name_plural = "event_references"
    display_name = "Event reference"
    display_name_plural = "Event references"
    create_view_class = None
    read_display_class = ReadDisplay
    update_form_class = UpdateEventReferenceForm
    delete_form_class = DeleteEventReferenceForm
    update_view_class = UpdateView
    delete_view_class = DeleteView
    list_display_class = ListDisplay
    list_view_class = ListView
    generic_prefix = "incoming_"

    def get_model_display_name(self):
        return lazy_gettext("Incoming reference")

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming references")

    def create_list_query(self, form, page_request, **kwargs):
        return ListIncomingEventReferencesQuery(
            admin_unit_id=current_admin_unit.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetIncomingEventReferenceQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__` (the model's display name).
        return f"{gettext(self.display_name)} {object.id}"

    def get_list_per_page(self):
        return 50

    def get_additional_read_actions(self, object):
        result = super().get_additional_read_actions(object)

        view_event_action = self._create_action(
            url_for(
                "main.event",
                event_id=object.event.id,
            ),
            gettext("View event"),
        )
        if view_event_action:
            result.append(view_event_action)

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
