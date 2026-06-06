"""Tests for AbstractUnitOfWork."""

import pytest

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.events.app_deleted import AppDeleted
from project.domain.events.app_updated import AppUpdated
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# Minimal concrete stub — no DB, no side effects
# ---------------------------------------------------------------------------


class _MockRepo:
    """Stub repository with a configurable .seen set."""

    def __init__(self):
        self.seen = set()


class _MockAggregate:
    """Stub aggregate that holds domain_events."""

    def __init__(self, events=None):
        self.domain_events = list(events or [])


class _ConcreteUoW(AbstractUnitOfWork):
    """Concrete UoW that wires up mock repos and records commit/rollback calls."""

    def __init__(self):
        self.events = _MockRepo()
        self.event_organizers = _MockRepo()
        self.event_references = _MockRepo()
        self.event_places = _MockRepo()
        self.organizations = _MockRepo()
        self.webhook_events = _MockRepo()
        self.webhook_deliveries = _MockRepo()
        self.webhook_delivery_attempts = _MockRepo()
        self.apps = _MockRepo()
        self.organization_app_installations = _MockRepo()
        self.organization_members = _MockRepo()
        self.users = _MockRepo()
        self.commit_called = False
        self.rollback_called = False

    def _commit(self):
        self.commit_called = True

    def rollback(self):
        self.rollback_called = True


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def uow():
    return _ConcreteUoW()


# ---------------------------------------------------------------------------
# __enter__ / __exit__
# ---------------------------------------------------------------------------


class TestUnitOfWorkContextManager:
    def test_enter_resets_pending_events(self, uow):
        uow.pending_events = ["stale"]
        with uow:
            assert uow.pending_events == []

    def test_enter_returns_self(self, uow):
        result = uow.__enter__()
        assert result is uow

    def test_exit_calls_rollback_on_normal_exit(self, uow):
        with uow:
            pass
        assert uow.rollback_called is True

    def test_exit_calls_rollback_on_exception(self, uow):
        with pytest.raises(ValueError):
            with uow:
                raise ValueError("boom")
        assert uow.rollback_called is True

    def test_exit_with_exception_clears_pending_events(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        with pytest.raises(ValueError):
            with uow:
                uow.pending_events.append(ev)
                raise ValueError("boom")
        assert uow.pending_events == []

    def test_exit_without_exception_keeps_pending_events(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        with uow:
            uow.pending_events.append(ev)
        # rollback was called but pending_events were NOT cleared
        assert ev in uow.pending_events


# ---------------------------------------------------------------------------
# commit()
# ---------------------------------------------------------------------------


class TestUnitOfWorkCommit:
    def test_commit_calls_internal_commit(self, uow):
        with uow:
            uow.commit()
        assert uow.commit_called is True

    def test_commit_collects_domain_events_from_repos(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        agg = _MockAggregate(events=[ev])
        uow.events.seen.add(agg)

        with uow:
            uow.commit()

        assert ev in uow.pending_events

    def test_commit_drains_aggregate_domain_events(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        agg = _MockAggregate(events=[ev])
        uow.events.seen.add(agg)

        with uow:
            uow.commit()

        assert agg.domain_events == []

    def test_commit_collects_from_all_repos(self, uow, actor):
        ev1 = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        ev2 = AppDeleted(actor=actor, id=2, admin_unit_id=3)
        agg1 = _MockAggregate(events=[ev1])
        agg2 = _MockAggregate(events=[ev2])
        uow.events.seen.add(agg1)
        uow.organizations.seen.add(agg2)

        with uow:
            uow.commit()

        assert ev1 in uow.pending_events
        assert ev2 in uow.pending_events


# ---------------------------------------------------------------------------
# collect_pending_events()
# ---------------------------------------------------------------------------


class TestCollectPendingEvents:
    def test_returns_copy_of_pending_events(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        with uow:
            uow.pending_events.append(ev)
            result = uow.collect_pending_events()
        assert ev in result

    def test_clears_pending_events_after_collect(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        with uow:
            uow.pending_events.append(ev)
            uow.collect_pending_events()
            assert uow.pending_events == []

    def test_returns_empty_list_when_no_events(self, uow):
        with uow:
            result = uow.collect_pending_events()
        assert result == []


# ---------------------------------------------------------------------------
# get_first_pending_event_by_type()
# ---------------------------------------------------------------------------


class TestGetFirstPendingEventByType:
    def test_returns_first_matching_event(self, uow, actor):
        ev1 = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        ev2 = AppUpdated(actor=actor, id=3, admin_unit_id=4)
        with uow:
            uow.pending_events.extend([ev1, ev2])
            result = uow.get_first_pending_event_by_type(AppDeleted)
        assert result is ev1

    def test_returns_none_when_no_matching_event(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        with uow:
            uow.pending_events.append(ev)
            result = uow.get_first_pending_event_by_type(AppUpdated)
        assert result is None


# ---------------------------------------------------------------------------
# _collect_domain_events_from_repo()
# ---------------------------------------------------------------------------


class TestCollectDomainEventsFromRepo:
    def test_drains_events_from_repo_seen(self, uow, actor):
        ev = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        agg = _MockAggregate(events=[ev])
        repo = _MockRepo()
        repo.seen.add(agg)

        with uow:
            uow._collect_domain_events_from_repo(repo)

        assert ev in uow.pending_events
        assert agg.domain_events == []

    def test_handles_empty_seen(self, uow):
        repo = _MockRepo()
        with uow:
            uow._collect_domain_events_from_repo(repo)
        assert uow.pending_events == []

    def test_collects_from_multiple_aggregates_in_seen(self, uow, actor):
        ev1 = AppDeleted(actor=actor, id=1, admin_unit_id=2)
        ev2 = AppDeleted(actor=actor, id=3, admin_unit_id=4)
        agg1 = _MockAggregate(events=[ev1])
        agg2 = _MockAggregate(events=[ev2])
        repo = _MockRepo()
        repo.seen.update([agg1, agg2])

        with uow:
            uow._collect_domain_events_from_repo(repo)

        assert ev1 in uow.pending_events
        assert ev2 in uow.pending_events
