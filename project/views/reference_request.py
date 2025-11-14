from flask_babel import gettext

from project.models import EventReferenceRequest, EventReferenceRequestReviewStatus
from project.services.admin_unit import get_admin_unit_by_id


def get_success_text_for_request_creation(request: EventReferenceRequest) -> str:
    admin_unit = (
        request.admin_unit
        if request.admin_unit
        else get_admin_unit_by_id(request.admin_unit_id)
    )

    if request.review_status == EventReferenceRequestReviewStatus.verified:
        return gettext(
            "%(organization)s accepted your reference request",
            organization=admin_unit.name,
        )

    return gettext(
        "Reference request to %(organization)s successfully created. You will be notified after the other organization reviews the event.",
        organization=admin_unit.name,
    )
