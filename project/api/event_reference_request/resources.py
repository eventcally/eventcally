from flask import abort, make_response
from flask_apispec import doc, marshal_with, use_kwargs
from marshmallow import ValidationError

from project import db
from project.access import access_or_401, has_access, login_api_user_or_401
from project.api import add_api_resource
from project.api.event_reference.schemas import EventReferenceIdSchema
from project.api.event_reference_request.schemas import (
    EventReferenceRequestRejectRequestSchema,
    EventReferenceRequestSchema,
    EventReferenceRequestVerifyRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import EventReferenceRequest
from project.models.event_reference_request import EventReferenceRequestReviewStatus
from project.services.reference import create_event_reference_for_request
from project.views.reference_request_review import (
    send_reference_request_review_status_mails,
)


class EventReferenceRequestResource(BaseResource):
    @doc(summary="Get event reference request", tags=["Event Reference Requests"])
    @marshal_with(EventReferenceRequestSchema)
    @require_api_access("eventreferencerequest:read")
    def get(self, id):
        login_api_user_or_401()
        reference_request = EventReferenceRequest.query.get_or_404(id)

        if not has_access(
            reference_request.event.admin_unit, "reference_request:read"
        ) and not has_access(reference_request.admin_unit, "reference_request:verify"):
            abort(401)

        return reference_request

    @doc(
        summary="Delete reference request",
        tags=["Event Reference Requests"],
    )
    @marshal_with(None, 204)
    @require_api_access("eventreferencerequest:write")
    def delete(self, id):
        login_api_user_or_401()
        reference_request = EventReferenceRequest.query.get_or_404(id)
        access_or_401(reference_request.event.admin_unit, "reference_request:delete")

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
    @require_api_access("eventreferencerequest:write")
    def post(self, id, **kwargs):
        login_api_user_or_401()
        reference_request = EventReferenceRequest.query.get_or_404(id)
        access_or_401(reference_request.admin_unit, "reference_request:verify")

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
    @require_api_access("eventreferencerequest:write")
    def post(self, id):
        login_api_user_or_401()
        reference_request = EventReferenceRequest.query.get_or_404(id)
        access_or_401(reference_request.admin_unit, "reference_request:verify")

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
