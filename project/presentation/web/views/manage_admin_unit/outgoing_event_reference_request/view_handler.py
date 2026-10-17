from flask_babel import lazy_gettext

from project.application.queries import (
    GetOutgoingEventReferenceRequestQuery,
    ListOutgoingEventReferenceRequestsQuery,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.presentation.shared.access import admin_unit_owner_access_or_401
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.modular.filters import (
    KeyEnumFilter,
    enum_filter_value_or_none,
)
from project.presentation.web.modular.sort_definition import KeySortDefinition
from project.presentation.web.views.manage_admin_unit import manage_admin_unit_bp
from project.presentation.web.views.manage_admin_unit.child_view_handler import (
    ManageAdminUnitChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.outgoing_event_reference_request.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.presentation.web.views.manage_admin_unit.outgoing_event_reference_request.views import (
    CreateView,
    ListView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    admin_unit_id_attribute_name = None
    model_name = "event_reference_request"
    model_name_plural = "event_reference_requests"
    display_name = "Event reference request"
    display_name_plural = "Event reference requests"
    create_view_class = None
    read_display_class = ReadDisplay
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_view_class = ListView
    list_filters = [
        KeyEnumFilter(
            "review_status",
            EventReferenceRequestReviewStatus,
            label=lazy_gettext("Review status"),
        ),
    ]
    list_sort_definitions = [
        KeySortDefinition("-created_at", label=lazy_gettext("Last created first")),
    ]
    generic_prefix = "outgoing_"

    def check_object_access(self, object):
        return admin_unit_owner_access_or_401(object.event.admin_unit.id)

    def get_model_display_name_plural(self):
        return lazy_gettext("Outgoing reference requests")

    def create_list_query(self, form, page_request, **kwargs):
        return ListOutgoingEventReferenceRequestsQuery(
            admin_unit_id=current_admin_unit.id,
            review_status=enum_filter_value_or_none(
                EventReferenceRequestReviewStatus, form.review_status.data
            ),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetOutgoingEventReferenceRequestQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"

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
            "create_for_event",
            f"/{single_url_folder}/create_for_event/<int:event_id>",
            CreateView,
            f"{single_endpoint_name}_create_for_event",
            app,
        )


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
