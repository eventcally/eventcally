from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs
from sqlalchemy import and_
from sqlalchemy.orm import lazyload, load_only

from project import db
from project.access import (
    access_or_401,
    can_read_event_or_401,
    can_read_private_events,
    login_api_user,
)
from project.api import add_api_resource, rest_api
from project.api.event.schemas import (
    EventListRequestSchema,
    EventListResponseSchema,
    EventPatchRequestSchema,
    EventPostRequestSchema,
    EventReportPostSchema,
    EventSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.api.schemas import NoneSchema
from project.models import AdminUnit, Event, EventDate, PublicStatus
from project.services.event import (
    get_event_with_details_or_404,
    get_events_query,
    get_significant_event_changes,
    update_event,
)
from project.services.search_params import EventSearchParams
from project.views.event import (
    send_event_report_mails,
    send_referenced_event_changed_mails,
)


def api_can_read_event_or_401(event: Event):
    if (
        event.public_status != PublicStatus.published
        or not event.admin_unit.is_verified
    ):
        login_api_user()
        can_read_event_or_401(event)


def api_can_read_private_events(admin_unit: AdminUnit):
    login_api_user()
    return can_read_private_events(admin_unit)


class EventListResource(BaseResource):
    @doc(summary="List events", tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        params = EventSearchParams()
        params.load_from_request(**kwargs)

        query = Event.query.join(Event.admin_unit).filter(
            and_(
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )
        )
        query = params.get_trackable_query(query, Event)
        query = params.get_trackable_order_by(query, Event)
        query = query.order_by(Event.min_start)

        return query.paginate()


class EventResource(BaseResource):
    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    @require_api_access()
    def get(self, id):
        login_api_user()
        event = get_event_with_details_or_404(id)
        api_can_read_event_or_401(event)
        return event

    @doc(
        summary="Update event",
        tags=["Events"],
    )
    @use_kwargs(EventPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", Event)
    def put(self, id):
        event = g.manage_admin_unit_instance
        event = self.update_instance(EventPostRequestSchema, instance=event)
        update_event(event)
        changes = get_significant_event_changes(event)
        db.session.commit()

        if changes:
            send_referenced_event_changed_mails(event)

        return make_response("", 204)

    @doc(
        summary="Patch event",
        tags=["Events"],
    )
    @use_kwargs(EventPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", Event)
    def patch(self, id):
        event = g.manage_admin_unit_instance
        event = self.update_instance(EventPatchRequestSchema, instance=event)
        update_event(event)
        changes = get_significant_event_changes(event)
        db.session.commit()

        if changes:
            send_referenced_event_changed_mails(event)

        return make_response("", 204)

    @doc(
        summary="Delete event",
        tags=["Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", Event)
    def delete(self, id):
        event = g.manage_admin_unit_instance
        event = Event.query.get_or_404(id)
        access_or_401(event.admin_unit, "events:write")

        db.session.delete(event)
        db.session.commit()

        return make_response("", 204)


class EventDatesResource(BaseResource):
    @doc(summary="List dates for event", tags=["Events", "Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        event = Event.query.options(
            load_only(Event.id, Event.public_status)
        ).get_or_404(id)
        api_can_read_event_or_401(event)

        return (
            EventDate.query.options(lazyload(EventDate.event))
            .filter(EventDate.event_id == event.id)
            .order_by(EventDate.start)
            .paginate()
        )


class EventSearchResource(BaseResource):
    @doc(summary="Search for events", tags=["Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        params = EventSearchParams()
        params.load_from_request(**kwargs)
        pagination = get_events_query(params).paginate()
        return pagination


class EventReportsResource(BaseResource):
    @doc(summary="Add event report", tags=["Events"])
    @use_kwargs(EventReportPostSchema, location="json", apply=False)
    @marshal_with(NoneSchema, 204)
    @require_api_access()
    def post(self, id):
        event = Event.query.options(
            load_only(Event.id, Event.public_status)
        ).get_or_404(id)
        api_can_read_event_or_401(event)

        report = EventReportPostSchema().load(request.json)
        send_event_report_mails(event, report)
        return make_response("", 204)


add_api_resource(EventListResource, "/events", "api_v1_event_list")
add_api_resource(EventResource, "/events/<int:id>", "api_v1_event")
add_api_resource(EventDatesResource, "/events/<int:id>/dates", "api_v1_event_dates")
add_api_resource(EventSearchResource, "/events/search", "api_v1_event_search")
rest_api.add_resource(
    EventReportsResource, "/events/<int:id>/reports", endpoint="api_v1_event_reports"
)
