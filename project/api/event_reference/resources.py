from flask import g, make_response
from flask_apispec import doc, marshal_with

from project import db
from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceSchema
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
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
    @require_organization_api_access(
        "organization.incoming_event_references:write", EventReference
    )
    def delete(self, id):
        reference = g.manage_admin_unit_instance
        db.session.delete(reference)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    EventReferenceResource, "/event-references/<int:id>", "api_v1_event_reference"
)
