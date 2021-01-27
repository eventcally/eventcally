from project.api import add_api_resource
from flask_apispec import marshal_with, doc
from project.api.resources import BaseResource
from project.api.organizer.schemas import OrganizerSchema
from project.models import EventOrganizer


class OrganizerResource(BaseResource):
    @doc(summary="Get organizer", tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    def get(self, id):
        return EventOrganizer.query.get_or_404(id)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
)
