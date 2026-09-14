from typing import Optional

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.services import ensure_organization_can_verify
from project.domain.types import ObjectId, unset

from .authorization_utils import ensure_actor_has_permission_for_admin_unit


def ensure_actor_can_verify_organization(
    uow: AbstractUnitOfWork,
    actor: Actor,
    verifier_admin_unit_id: ObjectId,
    verified_admin_unit_id: ObjectId,
) -> None:
    """Guard shared by `VerifyOrganizationHandler` and
    `ApproveOrganizationVerificationRequestHandler`: `actor` must be permitted
    to act for `verifier_admin_unit_id`, and `verified_admin_unit_id` must be
    verifiable by it. Both handlers call this right before
    `verify_organization_relation`.
    """
    ensure_actor_has_permission_for_admin_unit(
        actor,
        verifier_admin_unit_id,
        "incoming_organization_verification_requests:write",
        uow,
    )

    verified_admin_unit = uow.organizations.get(verified_admin_unit_id)
    verifier_admin_unit = uow.organizations.get(verifier_admin_unit_id)
    ensure_organization_can_verify(verified_admin_unit, verifier_admin_unit)


def ensure_organization_relation_exists(
    organization_relation_id: int, uow: AbstractUnitOfWork
) -> OrganizationRelationAggregate:
    organization_relation = uow.organization_relations.get(organization_relation_id)

    if not organization_relation:  # pragma: no cover
        raise NotFoundError(
            f"Organization relation with id {organization_relation_id} not found"
        )

    return organization_relation


def verify_organization_relation(
    uow: AbstractUnitOfWork,
    actor: Actor,
    source_admin_unit_id: ObjectId,
    target_admin_unit_id: ObjectId,
    auto_verify_event_reference_requests: Optional[bool] = None,
) -> OrganizationRelationAggregate:
    """Mark `source_admin_unit` as having verified `target_admin_unit`.

    Get-or-create the relation between the two organizations and set `verify`.
    Shared by the pure `VerifyOrganizationCommand` and by
    `ApproveOrganizationVerificationRequestCommand` (which resolves this
    function's arguments from the approved request before calling it) so both
    entry points run identical domain logic in their own transaction.
    """
    organization_relation = uow.organization_relations.get_by_source_and_target(
        source_admin_unit_id, target_admin_unit_id
    )

    if organization_relation is None:
        organization_relation = OrganizationRelationAggregate.create(
            actor=actor,
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
            verify=True,
            auto_verify_event_reference_requests=(
                auto_verify_event_reference_requests or False
            ),
        )
        uow.organization_relations.add(organization_relation)
    else:
        organization_relation.update(
            actor=actor,
            verify=True,
            auto_verify_event_reference_requests=(
                auto_verify_event_reference_requests
                if auto_verify_event_reference_requests is not None
                else unset
            ),
        )
        uow.organization_relations.update(organization_relation)

    return organization_relation
