"""Unit tests for organization verification request command handlers.

Also covers the `verify_organization_relation` domain-service function shared
by `VerifyOrganizationHandler` (no request involved) and
`ApproveOrganizationVerificationRequestHandler` (via a reviewed request) —
both should produce an equivalent relation for equivalent inputs.
"""

import pytest

from project.application import commands
from project.application.command_handlers.approve_organization_verification_request_handler import (
    ApproveOrganizationVerificationRequestHandler,
)
from project.application.command_handlers.reject_organization_verification_request_handler import (
    RejectOrganizationVerificationRequestHandler,
)
from project.application.command_handlers.request_organization_verification_handler import (
    RequestOrganizationVerificationHandler,
)
from project.application.command_handlers.verify_organization_handler import (
    VerifyOrganizationHandler,
)
from project.application.command_handlers.withdraw_organization_verification_request_handler import (
    WithdrawOrganizationVerificationRequestHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)

ACTOR_USER_ID = 1
ACTOR = Actor(user_id=ACTOR_USER_ID)


def _grant_permission(uow, admin_unit_id, permission, user_id=ACTOR_USER_ID):
    uow.organization_members.set_members_for(
        admin_unit_id,
        permission,
        [
            OrganisationMemberAggregate(
                id=admin_unit_id, admin_unit_id=admin_unit_id, user_id=user_id
            )
        ],
    )


def _seed_organizations(
    uow,
    source_admin_unit_id=1,
    target_admin_unit_id=2,
    target_can_verify_other=True,
    target_incoming_verification_requests_allowed=True,
    target_allowed_postal_codes=None,
    source_postal_code=None,
):
    """Seed the pair of organizations `ensure_organization_can_verify` reads.

    Naming here matches `ensure_organization_can_verify`'s own convention:
    `target_admin_unit_id` is the verifier (whose capability flags are
    checked), `source_admin_unit_id` is the one being verified (whose postal
    code is checked) — the opposite of `verify_organization_relation`'s
    source/target, which mean verifier/verified respectively.
    """
    uow.organizations.add(
        OrganizationAggregate(
            id=source_admin_unit_id,
            location=(
                LocationValueObject(postalCode=source_postal_code)
                if source_postal_code
                else None
            ),
        )
    )
    uow.organizations.add(
        OrganizationAggregate(
            id=target_admin_unit_id,
            can_verify_other=target_can_verify_other,
            incoming_verification_requests_allowed=(
                target_incoming_verification_requests_allowed
            ),
            incoming_verification_requests_postal_codes=(
                target_allowed_postal_codes or []
            ),
        )
    )


# ---------------------------------------------------------------------------
# RequestOrganizationVerificationHandler
# ---------------------------------------------------------------------------


class TestRequestOrganizationVerificationHandler:
    def test_creates_request_and_returns_result(self, uow):
        _grant_permission(uow, 1, "outgoing_organization_verification_requests:write")
        cmd = commands.RequestOrganizationVerificationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )

        result = RequestOrganizationVerificationHandler().handle(cmd, uow)

        assert result.id > 0
        created = uow.organization_verification_requests.get(result.id)
        assert created is not None
        assert created.source_admin_unit_id == 1
        assert created.target_admin_unit_id == 2

    def test_self_reference_raises_constraint_error(self, uow):
        _grant_permission(uow, 1, "outgoing_organization_verification_requests:write")
        cmd = commands.RequestOrganizationVerificationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=1
        )

        with pytest.raises(ConstraintError):
            RequestOrganizationVerificationHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        cmd = commands.RequestOrganizationVerificationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )

        with pytest.raises(UnauthorizedError):
            RequestOrganizationVerificationHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# VerifyOrganizationHandler and ApproveOrganizationVerificationRequestHandler
# share verify_organization_relation — assert both reach the same result.
#
# VerifyOrganizationCommand's source_admin_unit_id is the verifier (matching
# verify_organization_relation's convention), so its permission and capability
# checks are against source_admin_unit_id/target_admin_unit_id respectively —
# note _seed_organizations names its params the other way around
# (target_admin_unit_id = verifier), matching ensure_organization_can_verify.
# ---------------------------------------------------------------------------


class TestVerifyOrganizationHandler:
    def _grant_permission(self, uow, verifier_admin_unit_id=1):
        _grant_permission(
            uow,
            verifier_admin_unit_id,
            "incoming_organization_verification_requests:write",
        )

    def test_creates_relation_and_returns_result(self, uow):
        self._grant_permission(uow, verifier_admin_unit_id=1)
        _seed_organizations(uow, source_admin_unit_id=2, target_admin_unit_id=1)
        cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
        )

        result = VerifyOrganizationHandler().handle(cmd, uow)

        relation = uow.organization_relations.get(result.id)
        assert relation is not None
        assert relation.source_admin_unit_id == 1
        assert relation.target_admin_unit_id == 2
        assert relation.verify is True
        assert relation.auto_verify_event_reference_requests is True

    def test_verifying_twice_updates_the_same_relation(self, uow):
        self._grant_permission(uow, verifier_admin_unit_id=1)
        _seed_organizations(uow, source_admin_unit_id=2, target_admin_unit_id=1)
        cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )
        first = VerifyOrganizationHandler().handle(cmd, uow)

        cmd2 = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
        )
        second = VerifyOrganizationHandler().handle(cmd2, uow)

        assert first.id == second.id
        relation = uow.organization_relations.get(second.id)
        assert relation.auto_verify_event_reference_requests is True

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        _seed_organizations(uow, source_admin_unit_id=2, target_admin_unit_id=1)
        cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )

        with pytest.raises(UnauthorizedError):
            VerifyOrganizationHandler().handle(cmd, uow)

    def test_target_cannot_be_verified_by_source_raises_constraint_error(self, uow):
        self._grant_permission(uow, verifier_admin_unit_id=1)
        _seed_organizations(
            uow,
            source_admin_unit_id=2,
            target_admin_unit_id=1,
            target_can_verify_other=False,
        )
        cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )

        with pytest.raises(ConstraintError):
            VerifyOrganizationHandler().handle(cmd, uow)

    def test_platform_admin_bypasses_membership_check(self, uow):
        admin_user_id = 999
        uow.users.add(
            UserAggregate(
                id=admin_user_id,
                email="admin@test.de",
                locale=None,
                is_platform_admin=True,
            )
        )
        _seed_organizations(uow, source_admin_unit_id=2, target_admin_unit_id=1)
        cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=Actor(user_id=admin_user_id),
            source_admin_unit_id=1,
            target_admin_unit_id=2,
        )

        result = VerifyOrganizationHandler().handle(cmd, uow)

        assert result.id > 0


class TestApproveOrganizationVerificationRequestHandler:
    def _seed_request(self, uow, source_admin_unit_id=1, target_admin_unit_id=2):
        request = OrganizationVerificationRequestAggregate.create(
            actor=ACTOR,
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
        )
        uow.organization_verification_requests.add(request)
        return request

    def _grant_approve_permission(self, uow, target_admin_unit_id=2):
        _grant_permission(
            uow,
            target_admin_unit_id,
            "incoming_organization_verification_requests:write",
        )

    def test_approves_request_and_verifies_relation(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(uow, source_admin_unit_id=1, target_admin_unit_id=2)
        self._grant_approve_permission(uow, target_admin_unit_id=2)
        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id, auto_verify_event_reference_requests=True
        )

        result = ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

        approved = uow.organization_verification_requests.get(request.id)
        assert approved.review_status.name == "verified"

        # The relation is the other way around: the request's target (the
        # verifier) becomes the relation's source.
        relation = uow.organization_relations.get(result.id)
        assert relation is not None
        assert relation.source_admin_unit_id == 2
        assert relation.target_admin_unit_id == 1
        assert relation.verify is True
        assert relation.auto_verify_event_reference_requests is True

    def test_produces_same_relation_state_as_verify_organization_command(self, uow):
        """Both entry points share verify_organization_relation."""
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(uow, source_admin_unit_id=1, target_admin_unit_id=2)
        self._grant_approve_permission(uow, target_admin_unit_id=2)
        approve_cmd = (
            commands.ApproveOrganizationVerificationRequestCommand.model_construct(
                actor=ACTOR, id=request.id, auto_verify_event_reference_requests=True
            )
        )
        via_request_result = ApproveOrganizationVerificationRequestHandler().handle(
            approve_cmd, uow
        )
        via_request_relation = uow.organization_relations.get(via_request_result.id)

        _grant_permission(uow, 10, "incoming_organization_verification_requests:write")
        _seed_organizations(uow, source_admin_unit_id=20, target_admin_unit_id=10)
        verify_cmd = commands.VerifyOrganizationCommand.model_construct(
            actor=ACTOR,
            source_admin_unit_id=10,
            target_admin_unit_id=20,
            auto_verify_event_reference_requests=True,
        )
        direct_result = VerifyOrganizationHandler().handle(verify_cmd, uow)
        direct_relation = uow.organization_relations.get(direct_result.id)

        assert via_request_relation.verify == direct_relation.verify
        assert (
            via_request_relation.auto_verify_event_reference_requests
            == direct_relation.auto_verify_event_reference_requests
        )

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(uow, source_admin_unit_id=1, target_admin_unit_id=2)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

        # the request must not have been approved
        unchanged = uow.organization_verification_requests.get(request.id)
        assert unchanged.review_status.name == "inbox"

    def test_already_verified_raises_constraint_error(self, uow):
        request = self._seed_request(uow)
        _seed_organizations(uow)
        self._grant_approve_permission(uow)
        request.approve(ACTOR)
        uow.organization_verification_requests.update(request)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(ConstraintError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_approve_after_reject_succeeds(self, uow):
        request = self._seed_request(uow)
        _seed_organizations(uow)
        self._grant_approve_permission(uow)
        request.reject(ACTOR)
        uow.organization_verification_requests.update(request)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

        updated = uow.organization_verification_requests.get(request.id)
        assert updated.review_status.name == "verified"

    def test_target_cannot_verify_raises_constraint_error(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(
            uow,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            target_can_verify_other=False,
        )
        self._grant_approve_permission(uow, target_admin_unit_id=2)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(ConstraintError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

        # the request must not have been approved
        unchanged = uow.organization_verification_requests.get(request.id)
        assert unchanged.review_status.name == "inbox"

    def test_target_not_accepting_requests_raises_constraint_error(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(
            uow,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            target_incoming_verification_requests_allowed=False,
        )
        self._grant_approve_permission(uow, target_admin_unit_id=2)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(ConstraintError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_source_outside_allowed_postal_codes_raises_constraint_error(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(
            uow,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            target_allowed_postal_codes=["12345"],
            source_postal_code="99999",
        )
        self._grant_approve_permission(uow, target_admin_unit_id=2)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(ConstraintError):
            ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_source_inside_allowed_postal_codes_succeeds(self, uow):
        request = self._seed_request(
            uow, source_admin_unit_id=1, target_admin_unit_id=2
        )
        _seed_organizations(
            uow,
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            target_allowed_postal_codes=["12345"],
            source_postal_code="12345",
        )
        self._grant_approve_permission(uow, target_admin_unit_id=2)

        cmd = commands.ApproveOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        result = ApproveOrganizationVerificationRequestHandler().handle(cmd, uow)

        assert result.id > 0


# ---------------------------------------------------------------------------
# RejectOrganizationVerificationRequestHandler
# ---------------------------------------------------------------------------


class TestRejectOrganizationVerificationRequestHandler:
    def _seed_request(self, uow):
        request = OrganizationVerificationRequestAggregate.create(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )
        uow.organization_verification_requests.add(request)
        return request

    def test_rejects_request(self, uow):
        request = self._seed_request(uow)
        _grant_permission(uow, 2, "incoming_organization_verification_requests:write")
        cmd = commands.RejectOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR,
            id=request.id,
            rejection_reason=OrganizationVerificationRequestRejectionReason.unknown,
        )

        RejectOrganizationVerificationRequestHandler().handle(cmd, uow)

        rejected = uow.organization_verification_requests.get(request.id)
        assert rejected.review_status.name == "rejected"
        assert (
            rejected.rejection_reason
            == OrganizationVerificationRequestRejectionReason.unknown
        )

    def test_reject_after_reject_does_not_raise(self, uow):
        request = self._seed_request(uow)
        _grant_permission(uow, 2, "incoming_organization_verification_requests:write")
        cmd = commands.RejectOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR,
            id=request.id,
            rejection_reason=OrganizationVerificationRequestRejectionReason.unknown,
        )

        RejectOrganizationVerificationRequestHandler().handle(cmd, uow)
        RejectOrganizationVerificationRequestHandler().handle(cmd, uow)

        rejected = uow.organization_verification_requests.get(request.id)
        assert rejected.review_status.name == "rejected"

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.RejectOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            RejectOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        request = self._seed_request(uow)
        cmd = commands.RejectOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            RejectOrganizationVerificationRequestHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# WithdrawOrganizationVerificationRequestHandler
# ---------------------------------------------------------------------------


class TestWithdrawOrganizationVerificationRequestHandler:
    def _seed_request(self, uow):
        request = OrganizationVerificationRequestAggregate.create(
            actor=ACTOR, source_admin_unit_id=1, target_admin_unit_id=2
        )
        uow.organization_verification_requests.add(request)
        return request

    def test_removes_request(self, uow):
        request = self._seed_request(uow)
        _grant_permission(uow, 1, "outgoing_organization_verification_requests:write")

        cmd = commands.WithdrawOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        WithdrawOrganizationVerificationRequestHandler().handle(cmd, uow)

        assert uow.organization_verification_requests.get(request.id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.WithdrawOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            WithdrawOrganizationVerificationRequestHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        request = self._seed_request(uow)
        cmd = commands.WithdrawOrganizationVerificationRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            WithdrawOrganizationVerificationRequestHandler().handle(cmd, uow)
