from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import (
    DeleteCalendarCommand,
    RemoveEventFromCalendarCommand,
)
from project.application.queries import (
    GetCalendarQuery,
    ListCalendarsQuery,
    ResourceKind,
    SearchEventsQuery,
)
from project.presentation.api import add_api_resource
from project.presentation.api.calendar.schemas import (
    CalendarCreateRequestPlainSchema,
    CalendarEventAddRequestPlainSchema,
    CalendarIdPlainSchema,
    CalendarListRequestSchema,
    CalendarListResponseSchema,
    CalendarPatchRequestPlainSchema,
    CalendarPutRequestPlainSchema,
    CalendarSchema,
)
from project.presentation.api.event.schemas import (
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    organization_item_or_404,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.access import login_api_user
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.presentation.shared.query_args import (
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
)
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)

_TAGS = ["Organizations", "Calendars"]


class OrganizationCalendarListResource(BaseResource):
    @doc(summary="List calendars of organization", tags=_TAGS)
    @use_kwargs(CalendarListRequestSchema, location=("query"))
    @marshal_with(CalendarListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        login_api_user()  # private calendars are listed for members with calendars:read
        query = ListCalendarsQuery(
            admin_unit_id=id,
            name=kwargs.get("name"),
            sort=kwargs.get("sort"),
            trackable=trackable_criteria_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(summary="Add new calendar", tags=_TAGS)
    @use_kwargs(CalendarCreateRequestPlainSchema, location="json", apply=False)
    @marshal_with(CalendarIdPlainSchema, 201)
    @require_organization_api_access("organization.calendars:write")
    def post(self, id):
        cmd = CalendarCreateRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        cmd_result = self.message_bus.handle_command(cmd)
        return cmd_result, 201


class OrganizationCalendarResource(BaseResource):
    @doc(summary="Get calendar of organization", tags=_TAGS)
    @marshal_with(CalendarSchema)
    @require_api_access()
    def get(self, id, calendar_id):
        # A private calendar answers 404 unless the caller has calendars:read.
        login_api_user()
        result = result_or_404(self.query_bus.handle(GetCalendarQuery(id=calendar_id)))
        organization_item_or_404(self.query_bus, ResourceKind.calendar, id, calendar_id)
        return result

    @doc(summary="Update calendar", tags=_TAGS)
    @use_kwargs(CalendarPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.calendars:write",
        ResourceKind.calendar,
        item_arg="calendar_id",
    )
    def put(self, id, calendar_id):
        cmd = CalendarPutRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)
        return make_response("", 204)

    @doc(summary="Patch calendar", tags=_TAGS)
    @use_kwargs(CalendarPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.calendars:write",
        ResourceKind.calendar,
        item_arg="calendar_id",
    )
    def patch(self, id, calendar_id):
        cmd = CalendarPatchRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)
        return make_response("", 204)

    @doc(summary="Delete calendar", tags=_TAGS)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.calendars:write",
        ResourceKind.calendar,
        item_arg="calendar_id",
    )
    def delete(self, id, calendar_id):
        cmd = DeleteCalendarCommand(
            id=calendar_id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        return make_response("", 204)


class OrganizationCalendarEventListResource(BaseResource):
    @doc(summary="List events of calendar", tags=_TAGS + ["Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, id, calendar_id, **kwargs):
        login_api_user()
        result_or_404(self.query_bus.handle(GetCalendarQuery(id=calendar_id)))
        organization_item_or_404(self.query_bus, ResourceKind.calendar, id, calendar_id)

        page = self.query_bus.handle(
            SearchEventsQuery(
                criteria=event_search_criteria_from_request(
                    kwargs,
                    admin_unit_id=id,
                    include_private=True,
                    calendar_ids=[calendar_id],
                ),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page

    @doc(summary="Add event to calendar", tags=_TAGS + ["Events"])
    @use_kwargs(CalendarEventAddRequestPlainSchema, location="json", apply=False)
    @marshal_with(CalendarIdPlainSchema, 201)
    @require_organization_api_access(
        "organization.calendars:write",
        ResourceKind.calendar,
        item_arg="calendar_id",
    )
    def post(self, id, calendar_id):
        cmd = CalendarEventAddRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        return self.message_bus.handle_command(cmd), 201


class OrganizationCalendarEventResource(BaseResource):
    @doc(summary="Remove event from calendar", tags=_TAGS + ["Events"])
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.calendars:write",
        ResourceKind.calendar,
        item_arg="calendar_id",
    )
    def delete(self, id, calendar_id, event_id):
        cmd = RemoveEventFromCalendarCommand(
            calendar_id=calendar_id,
            event_id=event_id,
            actor=self.app_context_provider.get_current_actor(),
        )
        self.message_bus.handle_command(cmd)
        return make_response("", 204)


add_api_resource(
    OrganizationCalendarListResource,
    "/organizations/<int:id>/calendars",
    "api_v1_organization_calendar_list",
)
add_api_resource(
    OrganizationCalendarResource,
    "/organizations/<int:id>/calendars/<int:calendar_id>",
    "api_v1_organization_calendar",
)
add_api_resource(
    OrganizationCalendarEventListResource,
    "/organizations/<int:id>/calendars/<int:calendar_id>/events",
    "api_v1_organization_calendar_event_list",
)
add_api_resource(
    OrganizationCalendarEventResource,
    "/organizations/<int:id>/calendars/<int:calendar_id>/events/<int:event_id>",
    "api_v1_organization_calendar_event",
)
