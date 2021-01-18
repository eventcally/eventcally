from project.api import add_api_resource
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.event_category.schemas import (
    EventCategoryListRequestSchema,
    EventCategoryListResponseSchema,
)
from project.models import EventCategory


class EventCategoryListResource(MethodResource):
    @doc(summary="List event categories", tags=["Event Categories"])
    @use_kwargs(EventCategoryListRequestSchema, location=("query"))
    @marshal_with(EventCategoryListResponseSchema)
    def get(self, **kwargs):
        pagination = EventCategory.query.paginate()
        return pagination


add_api_resource(
    EventCategoryListResource, "/event-categories", "api_v1_event_category_list"
)
