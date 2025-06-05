from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.models import EventReferenceRequest
from project.models.event_reference_request import EventReferenceRequestReviewStatus
from project.modular.filters import EnumFilter
from project.modular.sort_definition import SortDefinition
from project.views.manage_admin_unit import manage_admin_unit_bp
from project.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.views.manage_admin_unit.incoming_event_reference_request.displays import (
    ListDisplay,
)
from project.views.manage_admin_unit.incoming_event_reference_request.views import (
    ListView,
    ReviewView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model = EventReferenceRequest
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_view_class = ListView
    list_filters = [
        EnumFilter(
            EventReferenceRequest.review_status, label=lazy_gettext("Review status")
        ),
    ]
    list_sort_definitions = [
        SortDefinition(
            EventReferenceRequest.created_at,
            desc=True,
            label=lazy_gettext("Last created first"),
        ),
    ]
    generic_prefix = "incoming_"

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming reference requests")

    def get_list_per_page(self):
        return 50

    def _add_views(
        self,
        app,
        single_url_folder,
        plural_url_folder,
        single_endpoint_name,
        plural_endpoint_name,
        id_query_arg_name,
    ):
        super()._add_views(
            app,
            single_url_folder,
            plural_url_folder,
            single_endpoint_name,
            plural_endpoint_name,
            id_query_arg_name,
        )

        self._add_view(
            "review",
            f"/{single_url_folder}/<int:{id_query_arg_name}>/review",
            ReviewView,
            f"{single_endpoint_name}_review",
            app,
        )

    def get_additional_list_actions(self, object):
        result = super().get_additional_list_actions(object)

        if object.review_status != EventReferenceRequestReviewStatus.verified:
            kwargs = dict()
            kwargs.setdefault(self.get_id_query_arg_name(), object.id)
            review_action = self._create_action(
                self.get_endpoint_url("review", **kwargs), gettext("Review request")
            )
            if review_action:
                result.append(review_action)

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
