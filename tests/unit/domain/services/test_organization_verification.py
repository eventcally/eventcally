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

    def test_raises_when_target_does_not_allow_incoming_requests(self):
        source = _org(1)
        target = _org(
            2, can_verify_other=True, incoming_verification_requests_allowed=False
        )

        with pytest.raises(ConstraintError):
            ensure_organization_can_verify(source, target)

    def test_passes_when_no_postal_code_restriction(self):
        source = _org(1)
        target = _org(
            2,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_postal_codes=[],
        )

        ensure_organization_can_verify(source, target)

    def test_raises_when_source_postal_code_not_allowed(self):
        source = _org(1, location=LocationValueObject(postalCode="99999"))
        target = _org(
            2,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_postal_codes=["12345"],
        )

        with pytest.raises(ConstraintError):
            ensure_organization_can_verify(source, target)

    def test_raises_when_source_has_no_location_but_target_restricts_postal_codes(
        self,
    ):
        source = _org(1)
        target = _org(
            2,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_postal_codes=["12345"],
        )

        with pytest.raises(ConstraintError):
            ensure_organization_can_verify(source, target)

    def test_passes_when_source_postal_code_allowed(self):
        source = _org(1, location=LocationValueObject(postalCode="12345"))
        target = _org(
            2,
            can_verify_other=True,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_postal_codes=["12345"],
        )

        ensure_organization_can_verify(source, target)
