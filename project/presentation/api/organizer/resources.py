from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import DeleteEventOrganizerCommand
from project.application.queries import GetEventOrganizerQuery, ResourceKind
from project.presentation.api import add_api_resource
from project.presentation.api.organizer.schemas import (
    OrganizerPatchRequestPlainSchema,
    OrganizerPutRequestPlainSchema,
    OrganizerSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


class OrganizerResource(BaseResource):
    @doc(summary="Get organizer", tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    @require_api_access()
    def get(self, id):
        return result_or_404(self.query_bus.handle(GetEventOrganizerQuery(id=id)))

    @doc(
        summary="Update organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", ResourceKind.event_organizer
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
        "organization.event_organizers:write", ResourceKind.event_organizer
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
        "organization.event_organizers:write", ResourceKind.event_organizer
    )
    def delete(self, id):
        cmd = DeleteEventOrganizerCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
)
