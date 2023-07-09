from flask import request
from flask_apispec import doc, marshal_with, use_kwargs
from sqlalchemy import and_
from sqlalchemy.orm import defaultload, lazyload

from project.access import can_use_planning, login_api_user
from project.api import add_api_resource
from project.api.event.resources import api_can_read_event_or_401
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
    EventDateSchema,
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnit, Event, EventDate, PublicStatus
from project.services.event import get_event_dates_query
from project.services.search_params import EventSearchParams
from project.views.utils import get_current_admin_unit_for_api


class EventDateListResource(BaseResource):
    @doc(summary="List event dates", tags=["Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        query = (
            EventDate.query.join(EventDate.event)
            .join(Event.admin_unit)
            .options(lazyload(EventDate.event))
            .filter(
                and_(
                    Event.public_status == PublicStatus.published,
                    AdminUnit.is_verified,
                )
            )
        )

        params = EventSearchParams()
        params.load_from_request(**kwargs)
        query = params.get_trackable_query(query, Event)
        query = params.get_trackable_order_by(query, Event)
        query = query.order_by(EventDate.start)
        return query.paginate()


class EventDateResource(BaseResource):
    @doc(summary="Get event date", tags=["Event Dates"])
    @marshal_with(EventDateSchema)
    @require_api_access()
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
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        params = EventSearchParams()
        params.include_admin_unit_references = True
        params.load_from_request(**kwargs)
        params.can_read_planned_events = can_use_planning()

        if "not_referenced" in request.args:
            admin_unit = get_current_admin_unit_for_api()

            if admin_unit:
                params.not_referenced_by_organization_id = admin_unit.id

        pagination = get_event_dates_query(params).paginate()
        return pagination


add_api_resource(EventDateListResource, "/event-dates", "api_v1_event_date_list")
add_api_resource(EventDateResource, "/event-dates/<int:id>", "api_v1_event_date")
add_api_resource(
    EventDateSearchResource, "/event-dates/search", "api_v1_event_date_search"
)
