from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from sqlalchemy.orm import lazyload, load_only

from project import db
from project.access import (
    access_or_401,
    can_read_event_or_401,
    can_read_private_events,
    login_api_user,
    login_api_user_or_401,
)
from project.api import add_api_resource
from project.api.event.schemas import (
    EventListRequestSchema,
    EventListResponseSchema,
    EventPatchRequestSchema,
    EventPostRequestSchema,
    EventSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.api.resources import BaseResource
from project.models import AdminUnit, Event, EventDate, PublicStatus
from project.oauth2 import require_oauth
from project.services.event import (
    get_event_with_details_or_404,
    get_events_query,
    get_significant_event_changes,
    update_event,
)
from project.services.event_search import EventSearchParams
from project.views.event import send_referenced_event_changed_mails


def api_can_read_event_or_401(event: Event):
    if event.public_status != PublicStatus.published:
        login_api_user()
        can_read_event_or_401(event)


def api_can_read_private_events(admin_unit: AdminUnit):
    login_api_user()
    return can_read_private_events(admin_unit)


class EventListResource(BaseResource):
    @doc(summary="List events", tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    def get(self, **kwargs):
        pagination = Event.query.filter(
            Event.public_status == PublicStatus.published
        ).paginate()
        return pagination


class EventResource(BaseResource):
    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    @require_oauth(optional=True)
    def get(self, id):
        event = get_event_with_details_or_404(id)
        api_can_read_event_or_401(event)
        return event

    @doc(
        summary="Update event", tags=["Events"], security=[{"oauth2": ["event:write"]}]
    )
    @use_kwargs(EventPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_oauth("event:write")
    def put(self, id):
        login_api_user_or_401()
        event = Event.query.get_or_404(id)
        access_or_401(event.admin_unit, "event:update")

        event = self.update_instance(EventPostRequestSchema, instance=event)
        update_event(event)
        changes = get_significant_event_changes(event)
        db.session.commit()

        if changes:
            send_referenced_event_changed_mails(event)

        return make_response("", 204)

    @doc(summary="Patch event", tags=["Events"], security=[{"oauth2": ["event:write"]}])
    @use_kwargs(EventPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_oauth("event:write")
    def patch(self, id):
        login_api_user_or_401()
        event = Event.query.get_or_404(id)
        access_or_401(event.admin_unit, "event:update")

        event = self.update_instance(EventPatchRequestSchema, instance=event)
        update_event(event)
        changes = get_significant_event_changes(event)
        db.session.commit()

        if changes:
            send_referenced_event_changed_mails(event)

        return make_response("", 204)

    @doc(
        summary="Delete event", tags=["Events"], security=[{"oauth2": ["event:write"]}]
    )
    @marshal_with(None, 204)
    @require_oauth("event:write")
    def delete(self, id):
        login_api_user_or_401()
        event = Event.query.get_or_404(id)
        access_or_401(event.admin_unit, "event:delete")

        db.session.delete(event)
        db.session.commit()

        return make_response("", 204)


class EventDatesResource(BaseResource):
    @doc(summary="List dates for event", tags=["Events", "Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    @require_oauth(optional=True)
    def get(self, id):
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
    def get(self, **kwargs):
        params = EventSearchParams()
        params.load_from_request()
        pagination = get_events_query(params).paginate()
        return pagination


add_api_resource(EventListResource, "/events", "api_v1_event_list")
add_api_resource(EventResource, "/events/<int:id>", "api_v1_event")
add_api_resource(EventDatesResource, "/events/<int:id>/dates", "api_v1_event_dates")
add_api_resource(EventSearchResource, "/events/search", "api_v1_event_search")
