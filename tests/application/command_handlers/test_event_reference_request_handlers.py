"""Unit tests for event reference request command handlers."""

from datetime import datetime, timezone

import pytest

from project.application import commands
from project.application.command_handlers.reject_event_reference_request_handler import (
    RejectEventReferenceRequestHandler,
)
from project.application.command_handlers.request_event_reference_handler import (
    RequestEventReferenceHandler,
)
from project.application.command_handlers.verify_event_reference_request_handler import (
    VerifyEventReferenceRequestHandler,
)
from project.application.command_handlers.withdraw_event_reference_request_handler import (
    WithdrawEventReferenceRequestHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from tests.application.conftest import ACTOR, grant_permission


def _make_event(uow, admin_unit_id=2, public_status=EventPublicStatus.published):
    event = EventAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Referenced Event",
        organizer_id=1,
        event_place_id=1,
        date_definitions=[
            EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
        ],
        status=EventStatus.scheduled,
        public_status=public_status,
    )
    uow.events.add(event)
    return event


def _make_request(uow, admin_unit_id, event_id, auto_verified=False):
    request = EventReferenceRequestAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        event_id=event_id,
        auto_verified=auto_verified,
    )
    uow.event_reference_requests.add(request)
    return request


def _make_reference(uow, admin_unit_id, event_id, rating=50):
    reference = EventReferenceAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        event_id=event_id,
        rating=rating,
    )
    uow.event_references.add(reference)
    return reference


# ---------------------------------------------------------------------------
# RequestEventReferenceHandler
# ---------------------------------------------------------------------------


class TestRequestEventReferenceHandler:
    def test_creates_inbox_request(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        grant_permission(uow, 2, "outgoing_event_reference_requests:write")
        cmd = commands.RequestEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id
        )

        result = RequestEventReferenceHandler().handle(cmd, uow)

        assert result.id > 0
        assert result.verified is False
        created = uow.event_reference_requests.get(result.id)
        assert created is not None
        assert created.admin_unit_id == 1
        assert created.event_id == event.id
        assert uow.event_references.get(1) is None

    def test_auto_verify_relation_creates_reference_and_verifies(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        grant_permission(uow, 2, "outgoing_event_reference_requests:write")
        relation = OrganizationRelationAggregate.create(
            actor=Actor(),
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
        )
        uow.organization_relations.add(relation)
        cmd = commands.RequestEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id
        )

        result = RequestEventReferenceHandler().handle(cmd, uow)

        assert result.verified is True
        created = uow.event_reference_requests.get(result.id)
        assert created.review_status.name == "verified"

        references = list(uow.event_references._store.values())
        assert len(references) == 1
        assert references[0].admin_unit_id == 1
        assert references[0].event_id == event.id

    def test_auto_verify_reuses_existing_reference(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        grant_permission(uow, 2, "outgoing_event_reference_requests:write")
        relation = OrganizationRelationAggregate.create(
            actor=Actor(),
            source_admin_unit_id=1,
            target_admin_unit_id=2,
            auto_verify_event_reference_requests=True,
        )
        uow.organization_relations.add(relation)
        existing = _make_reference(uow, admin_unit_id=1, event_id=event.id)
        cmd = commands.RequestEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id
        )

        result = RequestEventReferenceHandler().handle(cmd, uow)

        assert result.verified is True
        # A second reference would violate the (event, admin unit) unique
        # constraint and roll the whole command back.
        assert list(uow.event_references._store.values()) == [existing]

    def test_unpublished_event_raises_constraint_error(self, uow):
        event = _make_event(uow, admin_unit_id=2, public_status=EventPublicStatus.draft)
        grant_permission(uow, 2, "outgoing_event_reference_requests:write")
        cmd = commands.RequestEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id
        )

        with pytest.raises(ConstraintError):
            RequestEventReferenceHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        cmd = commands.RequestEventReferenceCommand.model_construct(
            actor=ACTOR, admin_unit_id=1, event_id=event.id
        )

        with pytest.raises(UnauthorizedError):
            RequestEventReferenceHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# VerifyEventReferenceRequestHandler
# ---------------------------------------------------------------------------


class TestVerifyEventReferenceRequestHandler:
    def test_verifies_and_creates_reference(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id, rating=70
        )

        result = VerifyEventReferenceRequestHandler().handle(cmd, uow)

        assert result.reference_id > 0
        updated = uow.event_reference_requests.get(request.id)
        assert updated.review_status.name == "verified"
        reference = uow.event_references.get(result.reference_id)
        assert reference.admin_unit_id == 1
        assert reference.event_id == event.id
        assert reference.rating == 70

    def test_reuses_existing_reference(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        existing = _make_reference(uow, admin_unit_id=1, event_id=event.id)
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id, rating=70
        )

        result = VerifyEventReferenceRequestHandler().handle(cmd, uow)

        assert result.reference_id == existing.id
        assert list(uow.event_references._store.values()) == [existing]
        updated = uow.event_reference_requests.get(request.id)
        assert updated.review_status.name == "verified"

    def test_auto_verify_creates_relation(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id, rating=70, auto_verify=True
        )

        VerifyEventReferenceRequestHandler().handle(cmd, uow)

        relation = uow.organization_relations.get_by_source_and_target(1, 2)
        assert relation is not None
        assert relation.auto_verify_event_reference_requests is True

    def test_already_verified_raises_constraint_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        VerifyEventReferenceRequestHandler().handle(cmd, uow)

        with pytest.raises(ConstraintError):
            VerifyEventReferenceRequestHandler().handle(cmd, uow)

    def test_verify_after_reject_succeeds(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        reject_cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        RejectEventReferenceRequestHandler().handle(reject_cmd, uow)

        verify_cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        VerifyEventReferenceRequestHandler().handle(verify_cmd, uow)

        updated = uow.event_reference_requests.get(request.id)
        assert updated.review_status.name == "verified"

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            VerifyEventReferenceRequestHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            VerifyEventReferenceRequestHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# RejectEventReferenceRequestHandler
# ---------------------------------------------------------------------------


class TestRejectEventReferenceRequestHandler:
    def test_rejects_with_reason(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR,
            id=request.id,
            rejection_reason=EventReferenceRequestRejectionReason.duplicate,
        )

        RejectEventReferenceRequestHandler().handle(cmd, uow)

        updated = uow.event_reference_requests.get(request.id)
        assert updated.review_status.name == "rejected"
        assert (
            updated.rejection_reason == EventReferenceRequestRejectionReason.duplicate
        )
        assert uow.event_references.get_by_event_id(event.id) == []

    def test_rejects_without_reason(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        RejectEventReferenceRequestHandler().handle(cmd, uow)

        updated = uow.event_reference_requests.get(request.id)
        assert updated.rejection_reason is None

    def test_auto_verify_creates_relation(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id, auto_verify=True
        )

        RejectEventReferenceRequestHandler().handle(cmd, uow)

        relation = uow.organization_relations.get_by_source_and_target(1, 2)
        assert relation is not None
        assert relation.auto_verify_event_reference_requests is True

    def test_reject_after_reject_does_not_raise(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        RejectEventReferenceRequestHandler().handle(cmd, uow)

        RejectEventReferenceRequestHandler().handle(cmd, uow)

        updated = uow.event_reference_requests.get(request.id)
        assert updated.review_status.name == "rejected"

    def test_already_verified_raises_constraint_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        grant_permission(uow, 1, "incoming_event_reference_requests:write")
        verify_cmd = commands.VerifyEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        VerifyEventReferenceRequestHandler().handle(verify_cmd, uow)

        reject_cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )
        with pytest.raises(ConstraintError):
            RejectEventReferenceRequestHandler().handle(reject_cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        cmd = commands.RejectEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            RejectEventReferenceRequestHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# WithdrawEventReferenceRequestHandler
# ---------------------------------------------------------------------------


class TestWithdrawEventReferenceRequestHandler:
    def test_removes_request(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        request_id = request.id
        grant_permission(uow, 2, "outgoing_event_reference_requests:write")
        cmd = commands.WithdrawEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request_id
        )

        WithdrawEventReferenceRequestHandler().handle(cmd, uow)

        assert uow.event_reference_requests.get(request_id) is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.WithdrawEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            WithdrawEventReferenceRequestHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        event = _make_event(uow, admin_unit_id=2)
        request = _make_request(uow, admin_unit_id=1, event_id=event.id)
        cmd = commands.WithdrawEventReferenceRequestCommand.model_construct(
            actor=ACTOR, id=request.id
        )

        with pytest.raises(UnauthorizedError):
            WithdrawEventReferenceRequestHandler().handle(cmd, uow)
