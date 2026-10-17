from flask import request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.queries import (
    GetEventDateDetailQuery,
    ListEventDatesQuery,
    SearchEventDatesQuery,
    TrackableSort,
)
from project.presentation.api import add_api_resource
from project.presentation.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
    EventDateSchema,
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.shared.access import login_api_user
from project.presentation.shared.current_admin_unit import (
    get_current_admin_unit_for_api,
)
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.presentation.shared.query_args import (
    enum_or_none,
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
)
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


class EventDateListResource(BaseResource):
    @doc(summary="List event dates", tags=["Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListEventDatesQuery(
                trackable=trackable_criteria_from_kwargs(kwargs),
                sort=enum_or_none(TrackableSort, kwargs.get("sort")),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class EventDateResource(BaseResource):
    @doc(summary="Get event date", tags=["Event Dates"])
    @marshal_with(EventDateSchema)
    @require_api_access()
    def get(self, id):
        login_api_user()
        return result_or_404(self.query_bus.handle(GetEventDateDetailQuery(id=id)))


class EventDateSearchResource(BaseResource):
    @doc(summary="Search for event dates", tags=["Event Dates"])
    @use_kwargs(EventDateSearchRequestSchema, location=("query"))
    @marshal_with(EventDateSearchResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        overrides = dict(include_planned=True)

        if "not_referenced" in request.args:
            admin_unit = get_current_admin_unit_for_api()

            if admin_unit:
                overrides["not_referenced_by_admin_unit_id"] = admin_unit.id

        page = self.query_bus.handle(
            SearchEventDatesQuery(
                criteria=event_search_criteria_from_request(
                    kwargs,
                    defaults=dict(include_admin_unit_references=True),
                    **overrides,
                ),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(EventDateListResource, "/event-dates", "api_v1_event_date_list")
add_api_resource(EventDateResource, "/event-dates/<int:id>", "api_v1_event_date")
add_api_resource(
    EventDateSearchResource, "/event-dates/search", "api_v1_event_date_search"
)
