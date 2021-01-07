from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event.schemas import (
    EventSchema,
    EventListRequestSchema,
    EventListResponseSchema,
)
from project.models import Event


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


rest_api.add_resource(EventListResource, "/events")
api_docs.register(EventListResource)

rest_api.add_resource(EventResource, "/events/<int:id>")
api_docs.register(EventResource)
