from flask_babel import lazy_gettext

from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.views.modular.base_display import BaseDisplay
from project.views.modular.base_props import (
    BadgePropFormatter,
    BaseProp,
    DateProp,
    EnumProp,
    EnumPropFormatter,
)


class AdminUnitVerificationRequestReviewStatusPropFormatter(BadgePropFormatter):
    # The domain enum is named differently; keep the ORM enum's msgids.
    enum_name = "AdminUnitVerificationRequestReviewStatus"
    badge_mapping = {
        OrganizationVerificationRequestReviewStatus.inbox: "info",
        OrganizationVerificationRequestReviewStatus.rejected: "danger",
        OrganizationVerificationRequestReviewStatus.verified: "success",
    }


class AdminUnitVerificationRequestRejectionReasonPropFormatter(EnumPropFormatter):
    enum_name = "AdminUnitVerificationRequestRejectionReason"


class ReadDisplay(BaseDisplay):
    target_admin_unit = BaseProp(lazy_gettext("Organization"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=AdminUnitVerificationRequestReviewStatusPropFormatter(),
    )
    rejection_reason = EnumProp(
        lazy_gettext("Rejection reason"),
        hide_when_empty=True,
        formatter=AdminUnitVerificationRequestRejectionReasonPropFormatter(),
    )


class ListDisplay(BaseDisplay):
    target_admin_unit = BaseProp(lazy_gettext("Organization"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=AdminUnitVerificationRequestReviewStatusPropFormatter(),
    )
    created_at = DateProp(lazy_gettext("Created at"))
