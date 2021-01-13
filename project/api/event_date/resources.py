from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event_date.schemas import (
    EventDateSchema,
    EventDateListRequestSchema,
    EventDateListResponseSchema,
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.models import EventDate
from project.services.event import get_event_dates_query
from project.services.event_search import EventSearchParams


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


class EventDateSearchResource(MethodResource):
    @doc(tags=["Event Dates"])
    @use_kwargs(EventDateSearchRequestSchema, location=("query"))
    @marshal_with(EventDateSearchResponseSchema)
    def get(self, **kwargs):
        params = EventSearchParams()
        params.load_from_request()
        pagination = get_event_dates_query(params).paginate()
        return pagination


rest_api.add_resource(EventDateListResource, "/event_dates")
api_docs.register(EventDateListResource)

rest_api.add_resource(EventDateResource, "/event_dates/<int:id>")
api_docs.register(EventDateResource)

rest_api.add_resource(EventDateSearchResource, "/event_dates/search")
api_docs.register(EventDateSearchResource)
