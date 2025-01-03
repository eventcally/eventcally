from flask import url_for
from flask_babel import gettext

from project.models import EventReference
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
from project.views.manage_admin_unit.incoming_event_reference.views import ListView
from project.views.utils import manage_permission_required


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventReference
    create_view_class = None
    read_decorators = [manage_permission_required("reference:read")]
    read_display_class = ReadDisplay
    update_decorators = [manage_permission_required("reference:update")]
    update_form_class = UpdateEventReferenceForm
    delete_decorators = [manage_permission_required("reference:delete")]
    delete_form_class = DeleteEventReferenceForm
    list_display_class = ListDisplay
    list_view_class = ListView
    generic_prefix = "incoming_"

    def get_model_display_name(self):
        return gettext("Incoming reference")

    def get_model_display_name_plural(self):
        return gettext("Incoming references")

    def apply_objects_query_order(self, query, **kwargs):
        return query.order_by(EventReference.created_at.desc())

    def get_list_per_page(self):
        return 50

    def get_additional_read_actions(self, object):
        result = super().get_additional_read_actions(object)

        view_event_action = self._create_action(
            url_for(
                "event",
                event_id=object.event.id,
            ),
            gettext("View event"),
        )
        if view_event_action:
            result.append(view_event_action)

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)