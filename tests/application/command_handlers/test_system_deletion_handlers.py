"""Unit tests for the system commands of the nightly purge jobs."""

import datetime

import pytest

from project.application import commands
from project.application.command_handlers import (
    DeleteGhostUserHandler,
    DeleteOldEventHandler,
    DeleteOrganizationDueForDeletionHandler,
    DeleteUserDueForDeletionHandler,
)
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor

SYSTEM = Actor()


def _ago(days):
    return datetime.datetime.utcnow() - datetime.timedelta(days=days)


def _org(uow, requested_at):
    org = OrganizationAggregate.create(actor=SYSTEM, name="Org", short_name="org")
    org.deletion_requested_at = requested_at
    uow.organizations.add(org)
    return org


def _user(uow, requested_at=None):
    user = UserAggregate(
        id=7, email="u@test.de", locale=None, deletion_requested_at=requested_at
    )
    uow.users.add(user)
    return user


class TestDeleteOrganizationDueForDeletionHandler:
    def _handle(self, uow, org_id):
        cmd = commands.DeleteOrganizationDueForDeletionCommand.model_construct(
            actor=SYSTEM, organization_id=org_id
        )
        return DeleteOrganizationDueForDeletionHandler().handle(cmd, uow)

    def test_due_is_removed_with_empty_actor(self, uow):
        org = _org(uow, _ago(4))

        assert self._handle(uow, org.id) is True
        assert uow.organizations.get(org.id) is None

    @pytest.mark.parametrize("requested_at", [_ago(1), None])
    def test_not_due_or_cancelled_is_kept(self, uow, requested_at):
        org = _org(uow, requested_at)

        assert self._handle(uow, org.id) is False
        assert uow.organizations.get(org.id) is not None

    def test_missing_is_noop(self, uow):
        assert self._handle(uow, 9999) is False


class TestDeleteUserDueForDeletionHandler:
    def _handle(self, uow, user_id):
        cmd = commands.DeleteUserDueForDeletionCommand.model_construct(
            actor=SYSTEM, user_id=user_id
        )
        return DeleteUserDueForDeletionHandler().handle(cmd, uow)

    def test_due_is_removed_with_empty_actor(self, uow):
        user = _user(uow, _ago(4))

        assert self._handle(uow, user.id) is True
        assert uow.users.get(user.id) is None

    @pytest.mark.parametrize("requested_at", [_ago(1), None])
    def test_not_due_or_cancelled_is_kept(self, uow, requested_at):
        user = _user(uow, requested_at)

        assert self._handle(uow, user.id) is False
        assert uow.users.get(user.id) is not None

    def test_missing_is_noop(self, uow):
        assert self._handle(uow, 9999) is False


class TestDeleteGhostUserHandler:
    def _handle(self, uow, user_id):
        cmd = commands.DeleteGhostUserCommand.model_construct(
            actor=SYSTEM, user_id=user_id
        )
        return DeleteGhostUserHandler().handle(cmd, uow)

    def test_removes_user(self, uow):
        user = _user(uow)

        assert self._handle(uow, user.id) is True
        assert uow.users.get(user.id) is None

    def test_missing_is_noop(self, uow):
        assert self._handle(uow, 9999) is False


class TestDeleteOldEventHandler:
    def _handle(self, uow, event_id):
        cmd = commands.DeleteOldEventCommand.model_construct(
            actor=SYSTEM, event_id=event_id
        )
        return DeleteOldEventHandler().handle(cmd, uow)

    def test_removes_event_silently(self, uow):
        event = EventAggregate.model_construct(id=5, domain_events=[])
        uow.events.add(event)

        assert self._handle(uow, 5) is True
        assert uow.events.get(5) is None
        assert uow.collect_pending_events() == []
        assert event.domain_events == []

    def test_missing_is_noop(self, uow):
        assert self._handle(uow, 9999) is False
