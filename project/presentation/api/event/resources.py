from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands.delete_event_command import DeleteEventCommand
from project.application.queries import (
    GetEventDetailQuery,
    ListEventDatesOfEventQuery,
    ListEventsQuery,
    ResourceKind,
    SearchEventsQuery,
    TrackableSort,
)
from project.presentation.api import add_api_resource
from project.presentation.api.event.schemas import (
    EventListRequestSchema,
    EventListResponseSchema,
    EventPatchRequestPlainSchema,
    EventPutRequestPlainSchema,
    EventReportPostSchema,
    EventSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.presentation.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.api.schemas import NoneSchema
from project.presentation.shared.access import login_api_user
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.presentation.shared.mail import send_event_report_mails
from project.presentation.shared.query_args import (
    enum_or_none,
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
)
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


class EventListResource(BaseResource):
    @doc(summary="List events", tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListEventsQuery(
                trackable=trackable_criteria_from_kwargs(kwargs),
                sort=enum_or_none(TrackableSort, kwargs.get("sort")),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class EventResource(BaseResource):

    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    @require_api_access()
    def get(self, id):
        login_api_user()
        return result_or_404(
            self.query_bus.handle(
                GetEventDetailQuery(
                    id=id, reference_admin_unit_id=reference_admin_unit_id_for_api()
                )
            )
        )

    @doc(
        summary="Update event",
        tags=["Events"],
    )
    @use_kwargs(EventPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def put(self, id):
        cmd = EventPutRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Patch event",
        tags=["Events"],
    )
    @use_kwargs(EventPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def patch(self, id):
        cmd = EventPatchRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Delete event",
        tags=["Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def delete(self, id):
        cmd = DeleteEventCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


class EventDatesResource(BaseResource):
    @doc(summary="List dates for event", tags=["Events", "Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        login_api_user()
        page = result_or_404(
            self.query_bus.handle(
                ListEventDatesOfEventQuery(
                    event_id=id, page=page_request_from_kwargs(kwargs)
                )
            )
        )
        abort_if_page_out_of_range(page)
        return page


class EventSearchResource(BaseResource):
    @doc(summary="Search for events", tags=["Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        page = self.query_bus.handle(
            SearchEventsQuery(
                criteria=event_search_criteria_from_request(kwargs),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class EventReportsResource(BaseResource):
    @doc(summary="Add event report", tags=["Events"])
    @use_kwargs(EventReportPostSchema, location="json", apply=False)
    @marshal_with(NoneSchema, 204)
    @require_api_access()
    def post(self, id):
        login_api_user()
        event = result_or_404(self.query_bus.handle(GetEventDetailQuery(id=id)))

        report = EventReportPostSchema().load(request.json)
        send_event_report_mails(event, report)
        return make_response("", 204)


add_api_resource(EventListResource, "/events", "api_v1_event_list")
add_api_resource(EventResource, "/events/<int:id>", "api_v1_event")
add_api_resource(EventDatesResource, "/events/<int:id>/dates", "api_v1_event_dates")
add_api_resource(EventSearchResource, "/events/search", "api_v1_event_search")
add_api_resource(
    EventReportsResource,
    "/events/<int:id>/reports",
    "api_v1_event_reports",
    api_docs=False,
)
