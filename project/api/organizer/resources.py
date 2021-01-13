from project import rest_api, api_docs
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.organizer.schemas import OrganizerSchema
from project.models import EventOrganizer


class OrganizerResource(MethodResource):
    @doc(tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    def get(self, id):
        return EventOrganizer.query.get_or_404(id)


rest_api.add_resource(
    OrganizerResource,
    "/organizers/<int:id>",
)
api_docs.register(OrganizerResource)
