from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)


def ensure_organization_verification_request_exists(
    verification_request_id: int, uow: AbstractUnitOfWork
) -> OrganizationVerificationRequestAggregate:
    verification_request = uow.organization_verification_requests.get(
        verification_request_id
    )

    if not verification_request:  # pragma: no cover
        raise NotFoundError(
            f"Organization verification request with id {verification_request_id} "
            "not found"
        )

    return verification_request
