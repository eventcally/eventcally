from flask import flash, url_for
from flask_babel import gettext

from project.models import EventPlace
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.event_place.displays import ListDisplay
from project.views.manage_admin_unit.event_place.forms import (
    CreateEventPlaceForm,
    DeleteEventPlaceForm,
    ListForm,
    UpdateEventPlaceForm,
)
from project.views.utils import (
    current_admin_unit,
    manage_permission_required,
    non_match_for_deletion,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventPlace
    create_decorators = [manage_permission_required("place:create")]
    create_form_class = CreateEventPlaceForm
    read_view_class = None
    update_decorators = [manage_permission_required("place:update")]
    update_form_class = UpdateEventPlaceForm
    delete_decorators = [manage_permission_required("place:delete")]
    delete_form_class = DeleteEventPlaceForm
    list_display_class = ListDisplay
    list_form_class = ListForm

    def get_list_per_page(self):
        return 50

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        view_events_action = self._create_action(
            url_for(
                "manage_admin_unit_events",
                id=current_admin_unit.id,
                event_place_id=object.id,
            ),
            gettext("View events"),
        )
        if view_events_action:
            result.append(view_events_action)

        return result

    def can_object_be_deleted(self, form, object):
        if non_match_for_deletion(form.name.data, object.name):
            flash(gettext("Entered name does not match place name"), "danger")
            return False
        return True


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
