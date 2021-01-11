from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event_category.schemas import (
    EventCategoryListRequestSchema,
    EventCategoryListResponseSchema,
)
from project.models import EventCategory


class EventCategoryListResource(MethodResource):
    @doc(tags=["Event Categories"])
    @use_kwargs(EventCategoryListRequestSchema, location=("query"))
    @marshal_with(EventCategoryListResponseSchema)
    def get(self, **kwargs):
        pagination = EventCategory.query.paginate()
        return pagination


rest_api.add_resource(EventCategoryListResource, "/event_categories")
api_docs.register(EventCategoryListResource)
