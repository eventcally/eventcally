from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)


def ensure_organization_member_exists(
    id: int, uow: AbstractUnitOfWork
) -> OrganisationMemberAggregate:
    member = uow.organization_members.get(id)

    if not member:  # pragma: no cover
        raise NotFoundError(f"Organization member with id {id} not found")

    return member
