from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.organizer.schemas import (
    OrganizerPatchRequestPlainSchema,
    OrganizerPutRequestPlainSchema,
    OrganizerSchema,
)
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.application.commands import DeleteEventOrganizerCommand
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
    @use_kwargs(OrganizerPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", EventOrganizer
    )
    def put(self, id):
        cmd = OrganizerPutRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)

    @doc(
        summary="Patch organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", EventOrganizer
    )
    def patch(self, id):
        cmd = OrganizerPatchRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        self.message_bus.handle_command(cmd)

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
        cmd = DeleteEventOrganizerCommand.model_construct(id=id)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
)
