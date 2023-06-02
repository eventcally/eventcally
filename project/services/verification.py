from sqlalchemy import and_
from sqlalchemy.orm import load_only

from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)


def get_verification_requests_incoming_query(admin_unit):
    return AdminUnitVerificationRequest.query.filter(
        and_(
            AdminUnitVerificationRequest.review_status
            != AdminUnitVerificationRequestReviewStatus.verified,
            AdminUnitVerificationRequest.target_admin_unit_id == admin_unit.id,
        )
    )


def get_verification_requests_incoming_badge_query(admin_unit):
    return AdminUnitVerificationRequest.query.options(
        load_only(AdminUnitVerificationRequest.id)
    ).filter(
        and_(
            AdminUnitVerificationRequest.review_status
            == AdminUnitVerificationRequestReviewStatus.inbox,
            AdminUnitVerificationRequest.target_admin_unit_id == admin_unit.id,
        )
    )
