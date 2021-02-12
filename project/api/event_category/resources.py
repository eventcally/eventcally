from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.event_category.schemas import (
    EventCategoryListRequestSchema,
    EventCategoryListResponseSchema,
)
from project.api.resources import BaseResource
from project.models import EventCategory


class EventCategoryListResource(BaseResource):
    @doc(summary="List event categories", tags=["Event Categories"])
    @use_kwargs(EventCategoryListRequestSchema, location=("query"))
    @marshal_with(EventCategoryListResponseSchema)
    def get(self, **kwargs):
        pagination = EventCategory.query.paginate()
        return pagination


add_api_resource(
    EventCategoryListResource, "/event-categories", "api_v1_event_category_list"
)
