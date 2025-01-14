from flask_babel import lazy_gettext

from project.models.admin_unit_verification_request import (
    AdminUnitVerificationRequestReviewStatus,
)
from project.modular.base_display import BaseDisplay
from project.modular.base_props import BadgePropFormatter, BaseProp, DateProp, EnumProp


class AdminUnitVerificationRequestReviewStatusPropFormatter(BadgePropFormatter):
    badge_mapping = {
        AdminUnitVerificationRequestReviewStatus.inbox: "info",
        AdminUnitVerificationRequestReviewStatus.rejected: "danger",
        AdminUnitVerificationRequestReviewStatus.verified: "success",
    }


class ReadDisplay(BaseDisplay):
    target_admin_unit = BaseProp(lazy_gettext("Organization"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=AdminUnitVerificationRequestReviewStatusPropFormatter(),
    )
    rejection_reason = EnumProp(lazy_gettext("Rejection reason"), hide_when_empty=True)


class ListDisplay(BaseDisplay):
    target_admin_unit = BaseProp(lazy_gettext("Organization"))
    review_status = EnumProp(
        lazy_gettext("Review status"),
        formatter=AdminUnitVerificationRequestReviewStatusPropFormatter(),
    )
    created_at = DateProp(lazy_gettext("Created at"))
