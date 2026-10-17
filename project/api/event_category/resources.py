from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.event_category.schemas import (
    EventCategoryListRequestSchema,
    EventCategoryListResponseSchema,
)
from project.api.query_args import page_request_from_kwargs
from project.api.resources import BaseResource, require_api_access
from project.application.queries import ListEventCategoriesQuery
from project.views.utils import abort_if_page_out_of_range


class EventCategoryListResource(BaseResource):
    @doc(summary="List event categories", tags=["Event Categories"])
    @use_kwargs(EventCategoryListRequestSchema, location=("query"))
    @marshal_with(EventCategoryListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListEventCategoriesQuery(page=page_request_from_kwargs(kwargs))
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    EventCategoryListResource, "/event-categories", "api_v1_event_category_list"
)
