from flask import make_response
from flask_apispec import doc, marshal_with

from project import db
from project.access import access_or_401, login_api_user_or_401
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

    @doc(
        summary="Delete reference",
        tags=["Event References"],
    )
    @marshal_with(None, 204)
    @require_api_access("eventreference:write")
    def delete(self, id):
        login_api_user_or_401()
        reference = EventReference.query.get_or_404(id)
        access_or_401(reference.admin_unit, "incoming_event_references:write")

        db.session.delete(reference)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    EventReferenceResource, "/event-references/<int:id>", "api_v1_event_reference"
)
