from flask_apispec import doc, marshal_with

from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceSchema
from project.api.resources import BaseResource, require_api_access
from project.models import EventReference


class EventReferenceResource(BaseResource):
    @doc(summary="Get event reference", tags=["Event References"])
    @marshal_with(EventReferenceSchema)
    @require_api_access()
    def get(self, id):
        return EventReference.query.get_or_404(id)


add_api_resource(
    EventReferenceResource, "/event-references/<int:id>", "api_v1_event_reference"
)
