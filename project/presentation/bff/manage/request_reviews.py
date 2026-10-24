from urllib.parse import quote_plus

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext, lazy_gettext

from project.application.commands import (
    ApproveOrganizationVerificationRequestCommand,
    RejectEventReferenceRequestCommand,
    RejectOrganizationVerificationRequestCommand,
    VerifyEventReferenceRequestCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetIncomingEventReferenceRequestReviewQuery,
    GetIncomingOrganizationVerificationRequestReviewQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    EventReferenceRequestReject,
    EventReferenceRequestReview,
    EventReferenceRequestVerify,
    OrganizationVerificationRequestApprove,
    OrganizationVerificationRequestReject,
    OrganizationVerificationRequestReview,
    RequestReviewed,
    ReviewChoice,
    ReviewCustomCategories,
    ReviewEvent,
    ReviewEventDate,
    ReviewEventOrganizer,
    ReviewEventPlace,
    ReviewOrganization,
    ReviewOrganizationMember,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.event_rating import event_rating_choices
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.urls import url_for_image
from project.shared.utils import (
    get_event_category_name,
    get_localized_enum_name,
    get_location_str,
    get_place_str,
)

# The order the old forms offered the reasons in.
_REFERENCE_REJECTION_REASONS = [
    (0, lazy_gettext("EventReferenceRequestRejectionReason.noreason")),
    (
        int(EventReferenceRequestRejectionReason.duplicate),
        lazy_gettext("EventReferenceRequestRejectionReason.duplicate"),
    ),
    (
        int(EventReferenceRequestRejectionReason.untrustworthy),
        lazy_gettext("EventReferenceRequestRejectionReason.untrustworthy"),
    ),
    (
        int(EventReferenceRequestRejectionReason.irrelevant),
        lazy_gettext("EventReferenceRequestRejectionReason.irrelevant"),
    ),
    (
        int(EventReferenceRequestRejectionReason.illegal),
        lazy_gettext("EventReferenceRequestRejectionReason.illegal"),
    ),
]
_VERIFICATION_REJECTION_REASONS = [
    (0, lazy_gettext("AdminUnitVerificationRequestRejectionReason.noreason")),
    (
        int(OrganizationVerificationRequestRejectionReason.notresponsible),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.notresponsible"),
    ),
    (
        int(OrganizationVerificationRequestRejectionReason.missinginformation),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.missinginformation"),
    ),
    (
        int(OrganizationVerificationRequestRejectionReason.unknown),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.unknown"),
    ),
    (
        int(OrganizationVerificationRequestRejectionReason.untrustworthy),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.untrustworthy"),
    ),
    (
        int(OrganizationVerificationRequestRejectionReason.illegal),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.illegal"),
    ),
    (
        int(OrganizationVerificationRequestRejectionReason.irrelevant),
        lazy_gettext("AdminUnitVerificationRequestRejectionReason.irrelevant"),
    ),
]


def _choices(pairs) -> list[ReviewChoice]:
    return [ReviewChoice(value=value, label=str(label)) for value, label in pairs]


def _reference_request_or_404(id: int, request_id: int, query_bus: QueryBus):
    review = result_or_404(
        query_bus.handle(
            GetIncomingEventReferenceRequestReviewQuery(actor=actor(), id=request_id)
        )
    )

    # Do not reveal the requests of other organizations.
    if review.admin_unit_id != id:
        abort(404)

    return review


def _verification_request_or_404(id: int, request_id: int, query_bus: QueryBus):
    review = result_or_404(
        query_bus.handle(
            GetIncomingOrganizationVerificationRequestReviewQuery(
                actor=actor(), id=request_id
            )
        )
    )

    if review.target_admin_unit_id != id:
        abort(404)

    return review


def _image_url(image, size: int):
    return url_for_image(image, s=size) if image else None


def _location_str(location):
    return get_location_str(location) or None


def _review_organization(organization) -> ReviewOrganization:
    return ReviewOrganization(
        id=organization.id,
        name=organization.name,
        is_verified=organization.is_verified,
        logo_url=_image_url(organization.logo, 120),
        description=organization.description,
        url=organization.url,
        email=organization.email,
        phone=organization.phone,
        fax=organization.fax,
        address=_location_str(organization.location),
    )


def _review_organizer(organizer) -> ReviewEventOrganizer:
    return ReviewEventOrganizer(
        name=organizer.name,
        logo_url=_image_url(organizer.logo, 120),
        url=organizer.url,
        email=organizer.email,
        phone=organizer.phone,
        fax=organizer.fax,
    )


def _shown_enum_label(value):
    """The label of an enum member, except the unset and the default (1) value, which
    the old page did not show."""
    if value and value.value > 1:
        return str(get_localized_enum_name(value))

    return None


def _review_event(event, start_definition) -> ReviewEvent:
    place = event.event_place
    attendance_mode = event.attendance_mode
    show_directions = attendance_mode and attendance_mode != EventAttendanceMode.offline

    return ReviewEvent(
        id=event.id,
        name=event.name,
        public_status=event.public_status.name if event.public_status else None,
        status=event.status.name if event.status else None,
        booked_up=event.booked_up,
        attendance_mode=attendance_mode.name if attendance_mode else None,
        start=start_definition.start if start_definition else None,
        end=start_definition.end if start_definition else None,
        allday=start_definition.allday if start_definition else False,
        status_label=_shown_enum_label(event.status),
        target_group_origin_label=_shown_enum_label(event.target_group_origin),
        attendance_mode_label=_shown_enum_label(attendance_mode),
        photo_url=_image_url(event.photo, 700),
        description=event.description,
        price_info=event.price_info,
        external_link=event.external_link,
        ticket_link=event.ticket_link,
        category_names=[str(get_event_category_name(c)) for c in event.categories],
        custom_categories=[
            ReviewCustomCategories(
                label=categories[0].category_set.label_or_name,
                names=[c.label_or_name for c in categories],
            )
            for categories in event.custom_categories_by_set.values()
        ],
        tags=event.tags,
        kid_friendly=event.kid_friendly,
        accessible_for_free=event.accessible_for_free,
        age_from=event.age_from,
        age_to=event.age_to,
        registration_required=event.registration_required,
        expected_participants=event.expected_participants,
        created_at=event.created_at,
        updated_at=event.updated_at,
        report_url=url_for("main.event_report", event_id=event.id),
        place=(
            ReviewEventPlace(
                name=place.name,
                photo_url=_image_url(place.photo, 300),
                description=place.description,
                url=place.url,
                address=_location_str(place.location),
                directions_url=(
                    "http://www.google.com/maps?q=" + quote_plus(get_place_str(place))
                    if show_directions
                    else None
                ),
            )
            if place
            else None
        ),
        organizer=_review_organizer(event.organizer) if event.organizer else None,
        co_organizers=[_review_organizer(o) for o in event.co_organizers],
        organization=_review_organization(event.admin_unit),
    )


def _reviewed(text: str, endpoint: str, id: int) -> RequestReviewed:
    flash(text, "success")
    return RequestReviewed(redirect_url=url_for(endpoint, id=id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-reference-requests/<int:request_id>/review",
    response=EventReferenceRequestReview,
    summary="Get an incoming reference request to review",
)
@inject
def get_incoming_event_reference_request_review(
    id: int,
    request_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    review = _reference_request_or_404(id, request_id, query_bus)
    event = review.event
    auto_verify = review.auto_verify

    return EventReferenceRequestReview(
        id=review.id,
        review_status=review.review_status.name,
        event=_review_event(event, event.min_start_definition),
        dates=[
            ReviewEventDate(id=date.id, start=date.start)
            for date in review.upcoming_dates
        ],
        auto_verify=auto_verify,
        auto_verify_description=(
            None
            if auto_verify
            else gettext(
                "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
                admin_unit_name=event.admin_unit.name,
            )
        ),
        rating_choices=_choices(event_rating_choices),
        rejection_reasons=_choices(_REFERENCE_REJECTION_REASONS),
        list_url=url_for("manage_admin_unit.incoming_event_reference_requests", id=id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-reference-requests/<int:request_id>/verify",
    method="POST",
    body=EventReferenceRequestVerify,
    response=RequestReviewed,
    summary="Accept an incoming reference request",
)
@inject
def verify_incoming_event_reference_request(
    id: int,
    request_id: int,
    body: EventReferenceRequestVerify,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _reference_request_or_404(id, request_id, query_bus)
    message_bus.handle_command(
        VerifyEventReferenceRequestCommand(
            actor=actor(),
            id=request_id,
            rating=body.rating,
            auto_verify=body.auto_verify,
        )
    )
    return _reviewed(
        gettext("Reference successfully created"),
        "manage_admin_unit.incoming_event_reference_requests",
        id,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-event-reference-requests/<int:request_id>/reject",
    method="POST",
    body=EventReferenceRequestReject,
    response=RequestReviewed,
    summary="Reject an incoming reference request",
)
@inject
def reject_incoming_event_reference_request(
    id: int,
    request_id: int,
    body: EventReferenceRequestReject,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _reference_request_or_404(id, request_id, query_bus)
    message_bus.handle_command(
        RejectEventReferenceRequestCommand(
            actor=actor(),
            id=request_id,
            rejection_reason=body.rejection_reason,
            auto_verify=False,
        )
    )
    return _reviewed(
        gettext("Request successfully updated"),
        "manage_admin_unit.incoming_event_reference_requests",
        id,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-verification-requests/<int:request_id>/review",
    response=OrganizationVerificationRequestReview,
    summary="Get an incoming verification request to review",
)
@inject
def get_incoming_verification_request_review(
    id: int,
    request_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    review = _verification_request_or_404(id, request_id, query_bus)
    organization = review.source_admin_unit

    return OrganizationVerificationRequestReview(
        id=review.id,
        review_status=review.review_status.name,
        organization=_review_organization(organization),
        members=[
            ReviewOrganizationMember(
                email=member.user.email,
                roles=[gettext(role.title) for role in member.roles],
            )
            for member in organization.members
        ],
        auto_verify_description=gettext(
            "If all upcoming reference requests of %(admin_unit_name)s should be verified automatically.",
            admin_unit_name=organization.name,
        ),
        rejection_reasons=_choices(_VERIFICATION_REJECTION_REASONS),
        list_url=url_for(
            "manage_admin_unit.incoming_organization_verification_requests", id=id
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-verification-requests/<int:request_id>/approve",
    method="POST",
    body=OrganizationVerificationRequestApprove,
    response=RequestReviewed,
    summary="Accept an incoming verification request",
)
@inject
def approve_incoming_verification_request(
    id: int,
    request_id: int,
    body: OrganizationVerificationRequestApprove,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _verification_request_or_404(id, request_id, query_bus)
    message_bus.handle_command(
        ApproveOrganizationVerificationRequestCommand(
            actor=actor(),
            id=request_id,
            auto_verify_event_reference_requests=body.auto_verify or None,
        )
    )
    return _reviewed(
        gettext("Organization successfully verified"),
        "manage_admin_unit.incoming_organization_verification_requests",
        id,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/incoming-verification-requests/<int:request_id>/reject",
    method="POST",
    body=OrganizationVerificationRequestReject,
    response=RequestReviewed,
    summary="Reject an incoming verification request",
)
@inject
def reject_incoming_verification_request(
    id: int,
    request_id: int,
    body: OrganizationVerificationRequestReject,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _verification_request_or_404(id, request_id, query_bus)
    message_bus.handle_command(
        RejectOrganizationVerificationRequestCommand(
            actor=actor(),
            id=request_id,
            rejection_reason=(
                OrganizationVerificationRequestRejectionReason(body.rejection_reason)
                if body.rejection_reason
                else None
            ),
        )
    )
    return _reviewed(
        gettext("Verification request successfully updated"),
        "manage_admin_unit.incoming_organization_verification_requests",
        id,
    )
