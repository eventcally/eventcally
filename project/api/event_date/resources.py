from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event_date.schemas import (
    EventDateSchema,
    EventDateListRequestSchema,
    EventDateListResponseSchema,
)
from project.models import EventDate


class EventDateListResource(MethodResource):
    @doc(tags=["Event Dates"])
    @use_kwargs(EventDateListRequestSchema, location=("query"))
    @marshal_with(EventDateListResponseSchema)
    def get(self, **kwargs):
        pagination = EventDate.query.paginate()
        return pagination


class EventDateResource(MethodResource):
    @doc(tags=["Event Dates"])
    @marshal_with(EventDateSchema)
    def get(self, id):
        return EventDate.query.get_or_404(id)


rest_api.add_resource(EventDateListResource, "/event_dates")
api_docs.register(EventDateListResource)

rest_api.add_resource(EventDateResource, "/event_dates/<int:id>")
api_docs.register(EventDateResource)
