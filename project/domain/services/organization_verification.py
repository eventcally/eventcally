from project.domain.errors import ConstraintError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)


def ensure_organization_can_verify(
    source_admin_unit: OrganizationAggregate, target_admin_unit: OrganizationAggregate
):
    """Raise unless `target_admin_unit` is currently able to verify
    `source_admin_unit`.

    Pure domain rule over two peer aggregates — it doesn't belong to either
    one alone, so it isn't a method on `OrganizationAggregate`. Callers are
    responsible for fetching both aggregates (via their unit of work) before
    calling this; re-run it at the moment of the state transition it guards,
    not just once when the underlying request was first created — these flags
    can change in between.
    """
    if (
        not target_admin_unit.can_verify_other
        or not target_admin_unit.incoming_verification_requests_allowed
    ):
        raise ConstraintError(
            "Target organization can no longer verify other organizations."
        )

    allowed_postal_codes = target_admin_unit.incoming_verification_requests_postal_codes
    if allowed_postal_codes:
        source_postal_code = (
            source_admin_unit.location.postalCode
            if source_admin_unit.location
            else None
        )
        if source_postal_code not in allowed_postal_codes:
            raise ConstraintError(
                "Source organization is outside the allowed postal codes."
            )
