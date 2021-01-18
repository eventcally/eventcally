from project.api import add_api_resource
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
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
from project.services.event import get_events_query
from project.services.event_search import EventSearchParams


class EventListResource(MethodResource):
    @doc(summary="List events", tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    def get(self, **kwargs):
        pagination = Event.query.paginate()
        return pagination


class EventResource(MethodResource):
    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    def get(self, id):
        return Event.query.get_or_404(id)


class EventDatesResource(MethodResource):
    @doc(summary="List dates for event", tags=["Events", "Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, id):
        event = Event.query.get_or_404(id)
        return EventDate.query.with_parent(event).paginate()


class EventSearchResource(MethodResource):
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
