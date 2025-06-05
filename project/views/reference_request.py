from flask_babel import gettext

from project.models import (
    Event,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
)
from project.models.event_reference import EventReference
from project.services.admin_unit import get_admin_unit_by_id, get_admin_unit_relation
from project.services.reference import create_event_reference_for_request
from project.views.utils import send_template_mails_to_admin_unit_members_async


def handle_request_according_to_relation(
    request: EventReferenceRequest, event: Event
) -> str:
    admin_unit = (
        request.admin_unit
        if request.admin_unit
        else get_admin_unit_by_id(request.admin_unit_id)
    )
    relation = get_admin_unit_relation(admin_unit.id, event.admin_unit_id)
    auto_verify = relation and relation.auto_verify_event_reference_requests
    reference = None

    if auto_verify:
        request.review_status = EventReferenceRequestReviewStatus.verified
        reference = create_event_reference_for_request(request)

        msg = gettext(
            "%(organization)s accepted your reference request",
            organization=admin_unit.name,
        )
    else:
        request.review_status = EventReferenceRequestReviewStatus.inbox

        msg = gettext(
            "Reference request to %(organization)s successfully created. You will be notified after the other organization reviews the event.",
            organization=admin_unit.name,
        )

    return reference, msg


def send_reference_request_mails(
    request: EventReferenceRequest, reference: EventReference
):
    if reference:
        _send_auto_reference_mails(reference)
    else:
        _send_reference_request_inbox_mails(request)


def _send_reference_request_inbox_mails(request):
    _send_member_reference_request_verify_mails(
        request.admin_unit_id,
        "reference_request_notice",
        request=request,
    )


def _send_auto_reference_mails(reference):
    _send_member_reference_request_verify_mails(
        reference.admin_unit_id,
        "reference_auto_verified_notice",
        reference=reference,
    )


def _send_member_reference_request_verify_mails(admin_unit_id, template, **context):
    # Benachrichtige alle Mitglieder der AdminUnit, die Requests verifizieren können
    send_template_mails_to_admin_unit_members_async(
        admin_unit_id, "incoming_event_reference_requests:write", template, **context
    )
