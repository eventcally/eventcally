from flask import g, make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project import db
from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceIdSchema
from project.api.event_reference_request.schemas import (
    EventReferenceRequestRejectRequestSchema,
    EventReferenceRequestSchema,
    EventReferenceRequestVerifyRequestSchema,
)
from project.api.resources import BaseResource, require_organization_api_access
from project.models import EventReferenceRequest
from project.models.event_reference_request import EventReferenceRequestReviewStatus
from project.services.reference import create_event_reference_for_request
from project.views.reference_request_review import (
    send_reference_request_review_status_mails,
)


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
        reference_request = g.manage_admin_unit_instance
        db.session.delete(reference_request)
        db.session.commit()

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
        reference_request = g.manage_admin_unit_instance

        if (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        ):  # pragma: no cover
            raise ValidationError("Request already verified")

        reference_request.review_status = EventReferenceRequestReviewStatus.verified

        reference = create_event_reference_for_request(reference_request)
        reference.rating = kwargs.get("rating", reference.rating)
        db.session.commit()

        send_reference_request_review_status_mails(reference_request)

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
        reference_request = g.manage_admin_unit_instance

        if (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        ):  # pragma: no cover
            raise ValidationError("Request already verified")

        reference_request = self.update_instance(
            EventReferenceRequestRejectRequestSchema, instance=reference_request
        )
        reference_request.review_status = EventReferenceRequestReviewStatus.rejected
        db.session.commit()

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
