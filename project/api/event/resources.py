from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event.schemas import (
    EventSchema,
    EventListRequestSchema,
    EventListResponseSchema,
)
from project.api.event_date.schemas import (
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.models import Event, EventDate


class EventListResource(MethodResource):
    @doc(tags=["Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    def get(self, **kwargs):
        pagination = Event.query.paginate()
        return pagination


class EventResource(MethodResource):
    @doc(tags=["Events"])
    @marshal_with(EventSchema)
    def get(self, id):
        return Event.query.get_or_404(id)


class EventDatesResource(MethodResource):
    @doc(tags=["Events"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, id):
        event = Event.query.get_or_404(id)
        return EventDate.query.with_parent(event).paginate()


rest_api.add_resource(EventListResource, "/events")
api_docs.register(EventListResource)

rest_api.add_resource(EventResource, "/events/<int:id>")
api_docs.register(EventResource)

rest_api.add_resource(EventDatesResource, "/events/<int:id>/dates")
api_docs.register(EventDatesResource)
