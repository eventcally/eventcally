import pytest

from project.domain.errors import ConstraintError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.services import ensure_organization_can_verify


def _org(id, **kwargs):
    return OrganizationAggregate(id=id, **kwargs)


class TestEnsureOrganizationCanVerify:
    def test_passes_when_target_can_verify(self):
        source = _org(1)
        target = _org(
            2, can_verify_other=True, incoming_verification_requests_allowed=True
        )

        ensure_organization_can_verify(source, target)

    def test_raises_when_target_cannot_verify_other(self):
        source = _org(1)
        target = _org(
            2, can_verify_other=False, incoming_verification_requests_allowed=True
        )

        with pytest.raises(ConstraintError):
            ensure_organization_can_verify(source, target)

    def test_ignores_incoming_requests_not_allowed(self):
        source = _org(1)
        target = _org(
            2, can_verify_other=True, incoming_verification_requests_allowed=False
        )

        ensure_organization_can_verify(source, target)

    @pytest.mark.parametrize(
        "location", [LocationValueObject(postalCode="99999"), None]
    )
    def test_ignores_postal_code_restriction(self, location):
        source = _org(1, location=location)
        target = _org(
            2,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_postal_codes=["12345"],
        )

        ensure_organization_can_verify(source, target)
