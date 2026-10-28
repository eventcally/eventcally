from flask import make_response
from flask_apispec import doc, marshal_with

from project.application.commands import DeleteEventReferenceCommand
from project.application.queries import GetEventReferenceQuery, ResourceKind
from project.presentation.api import add_api_resource
from project.presentation.api.event_reference.schemas import EventReferenceSchema
from project.presentation.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


def _get(resource, reference_id):
    return result_or_404(
        resource.query_bus.handle(GetEventReferenceQuery(id=reference_id))
    )


def _delete(resource, reference_id):
    cmd = DeleteEventReferenceCommand(
        id=reference_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


class EventReferenceResource(BaseResource):
    @doc(summary="Get event reference", tags=["Event References"])
    @marshal_with(EventReferenceSchema)
    @require_api_access()
    def get(self, id):
        return _get(self, id)

    @doc(
        summary="Delete reference",
        tags=["Event References"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_references:write", ResourceKind.event_reference
    )
    def delete(self, id):
        return _delete(self, id)


class OrganizationIncomingEventReferenceResource(BaseResource):
    @doc(summary="Get incoming event reference", tags=["Event References"])
    @marshal_with(EventReferenceSchema)
    @require_organization_api_access(
        "organization.incoming_event_references:read",
        ResourceKind.event_reference,
        item_arg="event_reference_id",
    )
    def get(self, id, event_reference_id):
        return _get(self, event_reference_id)

    @doc(
        summary="Delete reference",
        tags=["Event References"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_references:write",
        ResourceKind.event_reference,
        item_arg="event_reference_id",
    )
    def delete(self, id, event_reference_id):
        return _delete(self, event_reference_id)


class OrganizationOutgoingEventReferenceResource(BaseResource):
    @doc(summary="Get outgoing event reference", tags=["Event References"])
    @marshal_with(EventReferenceSchema)
    @require_organization_api_access(
        "organization.outgoing_event_references:read",
        ResourceKind.event_reference_event_owner,
        item_arg="event_reference_id",
    )
    def get(self, id, event_reference_id):
        return _get(self, event_reference_id)


add_api_resource(
    EventReferenceResource,
    "/event-references/<int:id>",
    "api_v1_event_reference",
    deprecated="/organizations/{id}/incoming-event-references/{event_reference_id} or /organizations/{id}/outgoing-event-references/{event_reference_id}",
)
add_api_resource(
    OrganizationIncomingEventReferenceResource,
    "/organizations/<int:id>/incoming-event-references/<int:event_reference_id>",
    "api_v1_organization_incoming_event_reference",
)
add_api_resource(
    OrganizationOutgoingEventReferenceResource,
    "/organizations/<int:id>/outgoing-event-references/<int:event_reference_id>",
    "api_v1_organization_outgoing_event_reference",
)
