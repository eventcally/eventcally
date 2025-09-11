from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project import db
from project.api import add_api_resource
from project.api.organizer.schemas import (
    OrganizerPatchRequestSchema,
    OrganizerPostRequestSchema,
    OrganizerSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.models import EventOrganizer


class OrganizerResource(BaseResource):
    @doc(summary="Get organizer", tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    @require_api_access()
    def get(self, id):
        return EventOrganizer.query.get_or_404(id)

    @doc(
        summary="Update organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", EventOrganizer
    )
    def put(self, id):
        organizer = g.manage_admin_unit_instance
        organizer = self.update_instance(OrganizerPostRequestSchema, instance=organizer)
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", EventOrganizer
    )
    def patch(self, id):
        organizer = g.manage_admin_unit_instance
        organizer = self.update_instance(
            OrganizerPatchRequestSchema, instance=organizer
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete organizer",
        tags=["Organizers"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", EventOrganizer
    )
    def delete(self, id):
        organizer = g.manage_admin_unit_instance
        db.session.delete(organizer)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
)
