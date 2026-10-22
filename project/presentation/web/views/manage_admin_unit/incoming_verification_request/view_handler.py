from flask import url_for
from flask_babel import gettext, lazy_gettext

from project.application.queries import (
    GetIncomingOrganizationVerificationRequestReviewQuery,
    ListIncomingOrganizationVerificationRequestsQuery,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
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
from project.presentation.web.views.manage_admin_unit.incoming_verification_request.displays import (
    ListDisplay,
)
from project.presentation.web.views.manage_admin_unit.incoming_verification_request.views import (
    ReviewView,
)


class ViewHandler(ManageAdminUnitChildViewHandler):
    model_name = "organization_verification_request"
    model_name_plural = "organization_verification_requests"
    display_name = "Organization verification request"
    display_name_plural = "Organization verification requests"
    admin_unit_id_attribute_name = "target_admin_unit_id"
    create_view_class = None
    read_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    list_filters = [
        KeyEnumFilter(
            "review_status",
            OrganizationVerificationRequestReviewStatus,
            enum_name="AdminUnitVerificationRequestReviewStatus",
            label=lazy_gettext("Review status"),
        ),
    ]
    list_sort_definitions = [
        KeySortDefinition("-created_at", label=lazy_gettext("Last created first")),
    ]
    generic_prefix = "incoming_"

    def create_list_query(self, form, page_request, **kwargs):
        return ListIncomingOrganizationVerificationRequestsQuery(
            admin_unit_id=current_admin_unit.id,
            review_status=enum_filter_value_or_none(
                OrganizationVerificationRequestReviewStatus, form.review_status.data
            ),
            page=page_request,
        )

    def create_get_query(self, object_id):
        return GetIncomingOrganizationVerificationRequestReviewQuery(id=object_id)

    def get_model_display_name_plural(self):
        return lazy_gettext("Incoming verification requests")

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

        if object.review_status != OrganizationVerificationRequestReviewStatus.verified:
            kwargs = dict()
            kwargs.setdefault(self.get_id_query_arg_name(), object.id)
            review_action = self._create_action(
                self.get_endpoint_url("review", **kwargs), gettext("Review request")
            )
            if review_action:
                result.append(review_action)

        view_organization_action = self._create_action(
            url_for("main.organization", id=object.source_admin_unit_id),
            gettext("View organization"),
        )
        if view_organization_action:
            result.append(view_organization_action)

        return result


handler = ViewHandler()
handler.init_app(manage_admin_unit_bp)
