from flask_apispec import doc, marshal_with, use_kwargs
from sqlalchemy import and_
from sqlalchemy.orm import defaultload, lazyload

from project.api import add_api_resource
from project.api.event.resources import api_can_read_event_or_401
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
    EventDateSchema,
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.api.resources import BaseResource
from project.models import AdminUnit, Event, EventDate, PublicStatus
from project.oauth2 import require_oauth
from project.services.event import get_event_dates_query
from project.services.event_search import EventSearchParams


class EventDateListResource(BaseResource):
    @doc(summary="List event dates", tags=["Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, **kwargs):
        pagination = (
            EventDate.query.join(EventDate.event)
            .join(Event.admin_unit)
            .options(lazyload(EventDate.event))
            .filter(
                and_(
                    Event.public_status == PublicStatus.published,
                    AdminUnit.is_verified,
                )
            )
            .paginate()
        )
        return pagination


class EventDateResource(BaseResource):
    @doc(summary="Get event date", tags=["Event Dates"])
    @marshal_with(EventDateSchema)
    @require_oauth(optional=True)
    def get(self, id):
        event_date = EventDate.query.options(
            defaultload(EventDate.event).load_only(
                Event.id, Event.name, Event.public_status
            )
        ).get_or_404(id)
        api_can_read_event_or_401(event_date.event)
        return event_date


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
