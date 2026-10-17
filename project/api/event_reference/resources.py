from flask import make_response
from flask_apispec import doc, marshal_with

from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceSchema
from project.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.application.commands import DeleteEventReferenceCommand
from project.application.queries import GetEventReferenceQuery, ResourceKind
from project.views.utils import result_or_404


class EventReferenceResource(BaseResource):
    @doc(summary="Get event reference", tags=["Event References"])
    @marshal_with(EventReferenceSchema)
    @require_api_access()
    def get(self, id):
        return result_or_404(self.query_bus.handle(GetEventReferenceQuery(id=id)))

    @doc(
        summary="Delete reference",
        tags=["Event References"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_references:write", ResourceKind.event_reference
    )
    def delete(self, id):
        cmd = DeleteEventReferenceCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    EventReferenceResource, "/event-references/<int:id>", "api_v1_event_reference"
)
