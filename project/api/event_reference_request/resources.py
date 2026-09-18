from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceIdSchema
from project.api.event_reference_request.schemas import (
    EventReferenceRequestRejectRequestPlainSchema,
    EventReferenceRequestRejectRequestSchema,
    EventReferenceRequestSchema,
    EventReferenceRequestVerifyRequestSchema,
)
from project.api.resources import BaseResource, require_organization_api_access
from project.application.commands import (
    VerifyEventReferenceRequestCommand,
    WithdrawEventReferenceRequestCommand,
)
from project.models import EventReference, EventReferenceRequest


class EventReferenceRequestResource(BaseResource):
    @doc(summary="Get event reference request", tags=["Event Reference Requests"])
    @marshal_with(EventReferenceRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read",
        EventReferenceRequest,
        admin_unit_id_path="event.admin_unit_id",
    )
    def get(self, id):
        reference_request = g.manage_admin_unit_instance
        return reference_request

    @doc(
        summary="Delete reference request",
        tags=["Event Reference Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:write",
        EventReferenceRequest,
        admin_unit_id_path="event.admin_unit_id",
    )
    def delete(self, id):
        cmd = WithdrawEventReferenceRequestCommand(
            id=id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


class EventReferenceRequestVerifyResource(BaseResource):
    @doc(
        summary="Verify event reference request. Returns reference id.",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestVerifyRequestSchema, location="json", apply=True)
    @marshal_with(EventReferenceIdSchema, 201)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write", EventReferenceRequest
    )
    def post(self, id, **kwargs):
        cmd = VerifyEventReferenceRequestCommand(
            id=id,
            rating=kwargs.get("rating", 50),
            actor=self.app_context_provider.get_current_actor(),
        )
        cmd_result = self.message_bus.handle_command(cmd)

        reference = EventReference.query.get(cmd_result.reference_id)
        return reference, 201


class EventReferenceRequestRejectResource(BaseResource):
    @doc(
        summary="Reject event reference request",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestRejectRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write", EventReferenceRequest
    )
    def post(self, id):
        cmd = self.load_command(EventReferenceRequestRejectRequestPlainSchema)
        self.message_bus.handle_command(cmd)

        return make_response("", 204)


add_api_resource(
    EventReferenceRequestResource,
    "/event-reference-requests/<int:id>",
    "api_v1_event_reference_request",
)
add_api_resource(
    EventReferenceRequestVerifyResource,
    "/event-reference-requests/<int:id>/verify",
    "api_v1_event_reference_request_verify",
)
add_api_resource(
    EventReferenceRequestRejectResource,
    "/event-reference-requests/<int:id>/reject",
    "api_v1_event_reference_request_reject",
)
