import datetime

from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.deletion_policy import DELETION_GRACE_PERIOD, is_deletion_due

NOW = datetime.datetime(2026, 10, 16, 12, 0, 0)


def test_none_is_not_due():
    assert is_deletion_due(None, NOW) is False


def test_within_grace_period_is_not_due():
    assert is_deletion_due(NOW - datetime.timedelta(days=2), NOW) is False


def test_exactly_at_boundary_is_not_due():
    assert is_deletion_due(NOW - DELETION_GRACE_PERIOD, NOW) is False


def test_after_grace_period_is_due():
    assert is_deletion_due(NOW - datetime.timedelta(days=4), NOW) is True


def test_aware_inputs_are_normalized():
    aware_now = NOW.replace(tzinfo=datetime.timezone.utc)
    requested = aware_now - datetime.timedelta(days=4)

    assert is_deletion_due(requested, aware_now) is True
    assert is_deletion_due(requested, NOW) is True
    assert is_deletion_due(requested.replace(tzinfo=None), aware_now) is True


def test_default_now_is_current_time():
    assert is_deletion_due(datetime.datetime.utcnow()) is False
    assert (
        is_deletion_due(datetime.datetime.utcnow() - datetime.timedelta(days=4)) is True
    )


def test_user_aggregate_delegates():
    user = UserAggregate(id=1, email="a@b.de", locale=None)
    assert user.is_deletion_due(NOW) is False

    user.deletion_requested_at = NOW - datetime.timedelta(days=4)
    assert user.is_deletion_due(NOW) is True


def test_organization_aggregate_delegates():
    org = OrganizationAggregate.model_construct(deletion_requested_at=None)
    assert org.is_deletion_due(NOW) is False

    org.deletion_requested_at = NOW - datetime.timedelta(days=4)
    assert org.is_deletion_due(NOW) is True
