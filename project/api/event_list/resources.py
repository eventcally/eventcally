from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project import db
from project.api import add_api_resource
from project.api.event.schemas import EventListRequestSchema, EventListResponseSchema
from project.api.event_list.schemas import (
    EventListPatchRequestSchema,
    EventListSchema,
    EventListUpdateRequestSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.models import Event, EventList
from project.services.event import get_events_query
from project.services.search_params import EventSearchParams


class EventListModelResource(BaseResource):
    @doc(summary="Get event list", tags=["Event Lists"])
    @marshal_with(EventListSchema)
    @require_api_access()
    def get(self, id):
        return EventList.query.get_or_404(id)

    @doc(
        summary="Update event list",
        tags=["Event Lists"],
    )
    @use_kwargs(EventListUpdateRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.event_lists:write", EventList)
    def put(self, id):
        event_list = g.manage_admin_unit_instance
        event_list = self.update_instance(
            EventListUpdateRequestSchema, instance=event_list
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch event list",
        tags=["Event Lists"],
    )
    @use_kwargs(EventListPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.event_lists:write", EventList)
    def patch(self, id):
        event_list = g.manage_admin_unit_instance
        event_list = self.update_instance(
            EventListPatchRequestSchema, instance=event_list
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete event list",
        tags=["Event Lists"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.event_lists:write", EventList)
    def delete(self, id):
        event_list = g.manage_admin_unit_instance
        db.session.delete(event_list)
        db.session.commit()

        return make_response("", 204)


class EventListEventListResource(BaseResource):
    @doc(
        summary="List events of event lists",
        tags=["Event Lists", "Events"],
    )
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        params = EventSearchParams()
        params.event_list_id = id
        pagination = get_events_query(params).paginate()
        return pagination


class EventListEventListWriteResource(BaseResource):
    @doc(
        summary="Add event",
        tags=["Event Lists", "Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.event_lists:write", EventList)
    def put(self, id, event_id):
        event_list = g.manage_admin_unit_instance
        event = Event.query.get_or_404(event_id)

        exists = (
            Event.query.with_parent(event_list).filter(Event.id == event_id).first()
        )
        if not exists:
            event_list.events.append(event)
            db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Remove event",
        tags=["Event Lists", "Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.event_lists:write", EventList)
    def delete(self, id, event_id):
        event_list = g.manage_admin_unit_instance
        event = Event.query.get_or_404(event_id)

        exists = (
            Event.query.with_parent(event_list).filter(Event.id == event_id).first()
        )
        if exists:
            event_list.events.remove(event)
            db.session.commit()

        return make_response("", 204)


add_api_resource(
    EventListModelResource, "/event-lists/<int:id>", "api_v1_event_list_model"
)

add_api_resource(
    EventListEventListResource,
    "/event-lists/<int:id>/events",
    "api_v1_event_list_event_list",
)

add_api_resource(
    EventListEventListWriteResource,
    "/event-lists/<int:id>/events/<int:event_id>",
    "api_v1_event_list_event_list_write",
)
