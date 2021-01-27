from project.api import add_api_resource
from flask_apispec import marshal_with, doc, use_kwargs
from project.api.resources import BaseResource
from project.api.event.schemas import (
    EventSchema,
    EventListRequestSchema,
    EventListResponseSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.models import Event, EventDate
from project.services.event import get_events_query, get_event_with_details_or_404
from project.services.event_search import EventSearchParams
from sqlalchemy.orm import lazyload, load_only


class EventListResource(BaseResource):
    @doc(summary="List events", tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    def get(self, **kwargs):
        pagination = Event.query.paginate()
        return pagination


class EventResource(BaseResource):
    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    def get(self, id):
        return get_event_with_details_or_404(id)


class EventDatesResource(BaseResource):
    @doc(summary="List dates for event", tags=["Events", "Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, id):
        event = Event.query.options(load_only(Event.id)).get_or_404(id)
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
