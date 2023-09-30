from sqlalchemy import and_
from sqlalchemy.orm import load_only

from project.models import (
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
)
from project.models.admin_unit import AdminUnit
from project.services.search_params import AdminUnitVerificationRequestSearchParams


def admin_unit_can_verify_admin_unit(
    source_admin_unit: AdminUnit, target_admin_unit: AdminUnit
):
    return (
        target_admin_unit.id != source_admin_unit.id
        and target_admin_unit.can_verify_other
        and target_admin_unit.incoming_verification_requests_allowed
        and (
            len(target_admin_unit.incoming_verification_requests_postal_codes) == 0
            or source_admin_unit.location.postalCode
            in target_admin_unit.incoming_verification_requests_postal_codes
        )
    )


def get_verification_requests_incoming_query(
    params: AdminUnitVerificationRequestSearchParams,
):
    result = AdminUnitVerificationRequest.query

    if params.target_admin_unit_id:
        result = result.filter(
            AdminUnitVerificationRequest.target_admin_unit_id
            == params.target_admin_unit_id
        )

    result = params.get_trackable_query(result, AdminUnitVerificationRequest)
    result = params.get_trackable_order_by(result, AdminUnitVerificationRequest)
    result = result.order_by(AdminUnitVerificationRequest.created_at.desc())
    return result


def get_verification_requests_outgoing_query(
    params: AdminUnitVerificationRequestSearchParams,
):
    result = AdminUnitVerificationRequest.query

    if params.source_admin_unit_id:
        result = result.filter(
            AdminUnitVerificationRequest.source_admin_unit_id
            == params.source_admin_unit_id
        )

    result = params.get_trackable_query(result, AdminUnitVerificationRequest)
    result = params.get_trackable_order_by(result, AdminUnitVerificationRequest)
    result = result.order_by(AdminUnitVerificationRequest.created_at.desc())
    return result


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
