from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)


def ensure_organization_exists(
    organization_id: int, uow: AbstractUnitOfWork
) -> OrganizationAggregate:
    organization = uow.organizations.get(organization_id)

    if not organization:  # pragma: no cover
        raise NotFoundError(f"Organization with id {organization_id} not found")

    return organization
