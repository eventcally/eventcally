from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.event_category.schemas import (
    EventCategoryListRequestSchema,
    EventCategoryListResponseSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import EventCategory


class EventCategoryListResource(BaseResource):
    @doc(summary="List event categories", tags=["Event Categories"])
    @use_kwargs(EventCategoryListRequestSchema, location=("query"))
    @marshal_with(EventCategoryListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        pagination = EventCategory.query.paginate()
        return pagination


add_api_resource(
    EventCategoryListResource, "/event-categories", "api_v1_event_category_list"
)
