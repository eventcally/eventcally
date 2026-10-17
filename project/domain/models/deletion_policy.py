import datetime
from typing import Optional

DELETION_GRACE_PERIOD = datetime.timedelta(days=3)


def _naive_utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def is_deletion_due(
    requested_at: Optional[datetime.datetime],
    now: Optional[datetime.datetime] = None,
) -> bool:
    """Whether a deletion request is older than the grace period. Timestamps are
    naive UTC in the database; aware values are normalized."""
    if requested_at is None:
        return False

    now = _naive_utc(now) if now else datetime.datetime.utcnow()
    return _naive_utc(requested_at) < now - DELETION_GRACE_PERIOD
