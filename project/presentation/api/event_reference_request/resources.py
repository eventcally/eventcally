from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import (
    VerifyEventReferenceRequestCommand,
    WithdrawEventReferenceRequestCommand,
)
from project.application.queries import (
    GetIncomingEventReferenceRequestQuery,
    GetOutgoingEventReferenceRequestQuery,
    ResourceKind,
)
from project.presentation.api import add_api_resource
from project.presentation.api.event_reference.schemas import EventReferenceIdSchema
from project.presentation.api.event_reference_request.schemas import (
    EventReferenceRequestRejectRequestPlainSchema,
    EventReferenceRequestRejectRequestSchema,
    EventReferenceRequestSchema,
    EventReferenceRequestVerifyRequestSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


def _get_outgoing(resource, request_id):
    return result_or_404(
        resource.query_bus.handle(GetOutgoingEventReferenceRequestQuery(id=request_id))
    )


def _get_incoming(resource, request_id):
    return result_or_404(
        resource.query_bus.handle(GetIncomingEventReferenceRequestQuery(id=request_id))
    )


def _withdraw(resource, request_id):
    cmd = WithdrawEventReferenceRequestCommand(
        id=request_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _verify(resource, request_id, kwargs):
    cmd = VerifyEventReferenceRequestCommand(
        id=request_id,
        rating=kwargs.get("rating", 50),
        actor=resource.app_context_provider.get_current_actor(),
    )
    cmd_result = resource.message_bus.handle_command(cmd)

    return {"id": cmd_result.reference_id}, 201


def _reject(resource):
    cmd = resource.load_command(EventReferenceRequestRejectRequestPlainSchema)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


class EventReferenceRequestResource(BaseResource):
    @doc(summary="Get event reference request", tags=["Event Reference Requests"])
    @marshal_with(EventReferenceRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read",
        ResourceKind.event_reference_request,
    )
    def get(self, id):
        return _get_outgoing(self, id)

    @doc(
        summary="Delete reference request",
        tags=["Event Reference Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:write",
        ResourceKind.event_reference_request,
    )
    def delete(self, id):
        return _withdraw(self, id)


class EventReferenceRequestVerifyResource(BaseResource):
    @doc(
        summary="Verify event reference request. Returns reference id.",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestVerifyRequestSchema, location="json", apply=True)
    @marshal_with(EventReferenceIdSchema, 201)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write",
        ResourceKind.event_reference_request_target,
    )
    def post(self, id, **kwargs):
        return _verify(self, id, kwargs)


class EventReferenceRequestRejectResource(BaseResource):
    @doc(
        summary="Reject event reference request",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestRejectRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write",
        ResourceKind.event_reference_request_target,
    )
    def post(self, id):
        return _reject(self)


class OrganizationOutgoingEventReferenceRequestResource(BaseResource):
    @doc(summary="Get event reference request", tags=["Event Reference Requests"])
    @marshal_with(EventReferenceRequestSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read",
        ResourceKind.event_reference_request,
        item_arg="event_reference_request_id",
    )
    def get(self, id, event_reference_request_id):
        return _get_outgoing(self, event_reference_request_id)

    @doc(
        summary="Delete reference request",
        tags=["Event Reference Requests"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:write",
        ResourceKind.event_reference_request,
        item_arg="event_reference_request_id",
    )
    def delete(self, id, event_reference_request_id):
        return _withdraw(self, event_reference_request_id)


class OrganizationIncomingEventReferenceRequestResource(BaseResource):
    @doc(
        summary="Get incoming event reference request",
        tags=["Event Reference Requests"],
    )
    @marshal_with(EventReferenceRequestSchema)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:read",
        ResourceKind.event_reference_request_target,
        item_arg="event_reference_request_id",
    )
    def get(self, id, event_reference_request_id):
        return _get_incoming(self, event_reference_request_id)


class OrganizationIncomingEventReferenceRequestVerifyResource(BaseResource):
    @doc(
        summary="Verify event reference request. Returns reference id.",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestVerifyRequestSchema, location="json", apply=True)
    @marshal_with(EventReferenceIdSchema, 201)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write",
        ResourceKind.event_reference_request_target,
        item_arg="event_reference_request_id",
    )
    def post(self, id, event_reference_request_id, **kwargs):
        return _verify(self, event_reference_request_id, kwargs)


class OrganizationIncomingEventReferenceRequestRejectResource(BaseResource):
    @doc(
        summary="Reject event reference request",
        tags=["Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestRejectRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:write",
        ResourceKind.event_reference_request_target,
        item_arg="event_reference_request_id",
    )
    def post(self, id, event_reference_request_id):
        return _reject(self)


_OUTGOING_ITEM = (
    "/organizations/<int:id>/outgoing-event-reference-requests"
    "/<int:event_reference_request_id>"
)
_INCOMING_ITEM = (
    "/organizations/<int:id>/incoming-event-reference-requests"
    "/<int:event_reference_request_id>"
)

add_api_resource(
    EventReferenceRequestResource,
    "/event-reference-requests/<int:id>",
    "api_v1_event_reference_request",
    deprecated="/organizations/{id}/outgoing-event-reference-requests/{event_reference_request_id}",
)
add_api_resource(
    EventReferenceRequestVerifyResource,
    "/event-reference-requests/<int:id>/verify",
    "api_v1_event_reference_request_verify",
    deprecated="/organizations/{id}/incoming-event-reference-requests/{event_reference_request_id}/verify",
)
add_api_resource(
    EventReferenceRequestRejectResource,
    "/event-reference-requests/<int:id>/reject",
    "api_v1_event_reference_request_reject",
    deprecated="/organizations/{id}/incoming-event-reference-requests/{event_reference_request_id}/reject",
)
add_api_resource(
    OrganizationOutgoingEventReferenceRequestResource,
    _OUTGOING_ITEM,
    "api_v1_organization_outgoing_event_reference_request",
)
add_api_resource(
    OrganizationIncomingEventReferenceRequestResource,
    _INCOMING_ITEM,
    "api_v1_organization_incoming_event_reference_request",
)
add_api_resource(
    OrganizationIncomingEventReferenceRequestVerifyResource,
    _INCOMING_ITEM + "/verify",
    "api_v1_organization_incoming_event_reference_request_verify",
)
add_api_resource(
    OrganizationIncomingEventReferenceRequestRejectResource,
    _INCOMING_ITEM + "/reject",
    "api_v1_organization_incoming_event_reference_request_reject",
)
