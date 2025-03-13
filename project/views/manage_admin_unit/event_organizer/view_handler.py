from flask import flash, url_for
from flask_babel import gettext
from sqlalchemy.sql import func

from project.models import EventOrganizer
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.event_organizer.displays import ListDisplay
from project.views.manage_admin_unit.event_organizer.forms import (
    CreateEventOrganizerForm,
    DeleteEventOrganizerForm,
    ListForm,
    UpdateEventOrganizerForm,
)
from project.views.utils import (
    current_admin_unit,
    manage_permission_required,
    non_match_for_deletion,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventOrganizer
    create_decorators = [manage_permission_required("organizer:create")]
    create_form_class = CreateEventOrganizerForm
    read_view_class = None
    update_decorators = [manage_permission_required("organizer:update")]
    update_form_class = UpdateEventOrganizerForm
    delete_decorators = [manage_permission_required("organizer:delete")]
    delete_form_class = DeleteEventOrganizerForm
    list_display_class = ListDisplay
    list_form_class = ListForm

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(func.lower(EventOrganizer.name))
        )

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_action = self._create_action(
            url_for(
                "organizers",
                path=object.id,
            ),
            gettext("View"),
        )
        if view_action:
            result.insert(0, view_action)

        view_events_action = self._create_action(
            url_for(
                "manage_admin_unit_events",
                id=current_admin_unit.id,
                organizer_id=object.id,
            ),
            gettext("View events"),
        )
        if view_events_action:
            result.append(view_events_action)

        return result

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.name):
            flash(gettext("Entered name does not match organizer name"), "danger")
            return False
        return True


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
