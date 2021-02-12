from flask_apispec import doc, marshal_with, use_kwargs
from sqlalchemy.orm import defaultload, lazyload

from project.api import add_api_resource
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
    EventDateSchema,
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.api.resources import BaseResource
from project.models import Event, EventDate
from project.services.event import get_event_dates_query
from project.services.event_search import EventSearchParams


class EventDateListResource(BaseResource):
    @doc(summary="List event dates", tags=["Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, **kwargs):
        pagination = EventDate.query.options(lazyload(EventDate.event)).paginate()
        return pagination


class EventDateResource(BaseResource):
    @doc(summary="Get event date", tags=["Event Dates"])
    @marshal_with(EventDateSchema)
    def get(self, id):
        return EventDate.query.options(
            defaultload(EventDate.event).load_only(Event.id, Event.name)
        ).get_or_404(id)


class EventDateSearchResource(BaseResource):
    @doc(summary="Search for event dates", tags=["Event Dates"])
    @use_kwargs(EventDateSearchRequestSchema, location=("query"))
    @marshal_with(EventDateSearchResponseSchema)
    def get(self, **kwargs):
        params = EventSearchParams()
        params.load_from_request()
        pagination = get_event_dates_query(params).paginate()
        return pagination


add_api_resource(EventDateListResource, "/event-dates", "api_v1_event_date_list")
add_api_resource(EventDateResource, "/event-dates/<int:id>", "api_v1_event_date")
add_api_resource(
    EventDateSearchResource, "/event-dates/search", "api_v1_event_date_search"
)
