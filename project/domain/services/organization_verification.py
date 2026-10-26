from project.domain.errors import ConstraintError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.translation import dummy_gettext


def ensure_organization_can_verify(
    source_admin_unit: OrganizationAggregate, target_admin_unit: OrganizationAggregate
):
    """Raise unless `target_admin_unit` is currently able to verify other
    organizations (`can_verify_other`).

    Pure domain rule over two peer aggregates — it doesn't belong to either
    one alone, so it isn't a method on `OrganizationAggregate`. Callers are
    responsible for fetching both aggregates (via their unit of work) before
    calling this; re-run it at the moment of the state transition it guards,
    because the flag can change after a request was created.

    `incoming_verification_requests_allowed` and
    `incoming_verification_requests_postal_codes` are deliberately not checked
    here: they only decide who may *create* a request
    (`CanRequestVerificationQuery` / `ListVerifierOrganizationsQuery`), so a
    verifier can still approve requests it already received after it turned
    incoming requests off or changed its postal codes.

    `source_admin_unit` is unused for now; it is kept for the peer-rule shape
    and for callers.
    """
    if not target_admin_unit.can_verify_other:
        raise ConstraintError(
            dummy_gettext(
                "Target organization can no longer verify other organizations."
            )
        )
