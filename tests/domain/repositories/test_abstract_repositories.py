"""
Tests for all abstract repository classes.

Each abstract repository is tested via a minimal concrete stub that
implements the abstract private methods with no-op or configurable returns.
No database or Flask app context is required.
"""

from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.domain.repositories.abstract_app_repository import AbstractAppRepository
from project.domain.repositories.abstract_event_organizer_repository import (
    AbstractEventOrganizerRepository,
)
from project.domain.repositories.abstract_event_place_repository import (
    AbstractEventPlaceRepository,
)
from project.domain.repositories.abstract_event_reference_repository import (
    AbstractEventReferenceRepository,
)
from project.domain.repositories.abstract_event_repository import (
    AbstractEventRepository,
)
from project.domain.repositories.abstract_organization_app_installation_repository import (
    AbstractOrganizationAppInstallationRepository,
)
from project.domain.repositories.abstract_organization_member_repository import (
    AbstractOrganizationMemberRepository,
)
from project.domain.repositories.abstract_organization_repository import (
    AbstractOrganizationRepository,
)
from project.domain.repositories.abstract_webhook_delivery_attempt_repository import (
    AbstractWebhookDeliveryAttemptRepository,
)
from project.domain.repositories.abstract_webhook_delivery_repository import (
    AbstractWebhookDeliveryRepository,
)
from project.domain.repositories.abstract_webhook_event_repository import (
    AbstractWebhookEventRepository,
)

# ---------------------------------------------------------------------------
# Concrete stubs
# ---------------------------------------------------------------------------


class _ConcreteEventRepo(AbstractEventRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, event):
        pass

    def _update(self, event):
        pass

    def _get(self, object_id):
        return self._return_value

    def _remove(self, event):
        pass


class _ConcreteEventOrganizerRepo(AbstractEventOrganizerRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, e):
        pass

    def _update(self, e):
        pass

    def _get(self, oid):
        return self._return_value

    def _remove(self, e):
        pass


class _ConcreteEventPlaceRepo(AbstractEventPlaceRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, e):
        pass

    def _update(self, e):
        pass

    def _get(self, oid):
        return self._return_value

    def _remove(self, e):
        pass


class _ConcreteEventReferenceRepo(AbstractEventReferenceRepository):
    def __init__(self, return_values=None):
        super().__init__()
        self._return_values = return_values or []

    def _get_by_event_id(self, event_id):
        return self._return_values


class _ConcreteOrganizationRepo(AbstractOrganizationRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _get(self, oid):
        return self._return_value

    def _update(self, org):
        pass


class _ConcreteAppRepo(AbstractAppRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, e):
        pass

    def _update(self, e):
        pass

    def _get(self, oid):
        return self._return_value

    def _remove(self, e):
        pass


class _ConcreteOrgAppInstallationRepo(AbstractOrganizationAppInstallationRepository):
    def __init__(self, return_value=None, all_with_webhook=None):
        super().__init__()
        self._return_value = return_value
        self._all_with_webhook = all_with_webhook or []

    def _add(self, e):
        pass

    def _update(self, e):
        pass

    def _get(self, oid):
        return self._return_value

    def _remove(self, e):
        pass

    def _get_all_with_webhook(self, admin_unit_id, event_type):
        return self._all_with_webhook


class _ConcreteOrgMemberRepo(AbstractOrganizationMemberRepository):
    def __init__(self, return_values=None):
        super().__init__()
        self._return_values = return_values or []

    def _get_all_with_permission(self, admin_unit_id, permission):
        return self._return_values


class _ConcreteWebhookDeliveryRepo(AbstractWebhookDeliveryRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, e):
        pass

    def _get(self, oid):
        return self._return_value


class _ConcreteWebhookDeliveryAttemptRepo(AbstractWebhookDeliveryAttemptRepository):
    def __init__(self, return_value=None):
        super().__init__()
        self._return_value = return_value

    def _add(self, e):
        pass

    def _get(self, oid):
        return self._return_value


class _ConcreteWebhookEventRepo(AbstractWebhookEventRepository):
    def __init__(self, return_value=None, deleted_count=0):
        super().__init__()
        self._return_value = return_value
        self._deleted_count = deleted_count

    def _add(self, e):
        pass

    def _get(self, oid):
        return self._return_value

    def _delete_old_events(self, days):
        return self._deleted_count


# ---------------------------------------------------------------------------
# Helper aggregates (constructed without going through create() factory to
# avoid domain event baggage)
# ---------------------------------------------------------------------------


def _event_agg():
    return EventAggregate.model_construct(id=1, domain_events=[])


def _organizer_agg():
    return EventOrganizerAggregate.model_construct(id=1, domain_events=[])


def _place_agg():
    return EventPlaceAggregate.model_construct(id=1, domain_events=[])


def _ref_agg(event_id=10):
    return EventReferenceAggregate.model_construct(
        id=1, admin_unit_id=2, event_id=event_id, domain_events=[]
    )


def _org_agg():
    return OrganizationAggregate.model_construct(id=1, domain_events=[])


def _app_agg():
    return AppAggregate.model_construct(id=1, domain_events=[])


def _installation_agg(permissions=None):
    return OrganisationAppInstallationAggregate.model_construct(
        id=1,
        admin_unit_id=2,
        app_id=3,
        permissions=permissions or [],
        domain_events=[],
    )


def _member_agg():
    return OrganisationMemberAggregate.model_construct(
        id=1, admin_unit_id=2, user_id=3, domain_events=[]
    )


def _delivery_agg():
    return WebhookDeliveryAggregate.model_construct(
        id=1, webhook_event_id=2, webhook_id=3, domain_events=[]
    )


def _attempt_agg():
    import datetime

    now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    return WebhookDeliveryAttemptAggregate.model_construct(
        id=1,
        url="https://x",
        start_at=now,
        end_at=now,
        webhook_delivery_id=1,
        domain_events=[],
    )


def _webhook_event_agg():
    import datetime

    return WebhookEventAggregate.model_construct(
        id=1,
        timestamp=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        event_type="x",
        payload={},
        domain_events=[],
    )


# ---------------------------------------------------------------------------
# AbstractEventRepository
# ---------------------------------------------------------------------------


class TestAbstractEventRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteEventRepo()
        agg = _event_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_update_adds_to_seen(self):
        repo = _ConcreteEventRepo()
        agg = _event_agg()
        repo.update(agg)
        assert agg in repo.seen

    def test_remove_adds_to_seen(self):
        repo = _ConcreteEventRepo()
        agg = _event_agg()
        repo.remove(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _event_agg()
        repo = _ConcreteEventRepo(return_value=agg)
        result = repo.get(1)
        assert result is agg
        assert agg in repo.seen

    def test_get_with_none_result_does_not_add_to_seen(self):
        repo = _ConcreteEventRepo(return_value=None)
        result = repo.get(1)
        assert result is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractEventOrganizerRepository
# ---------------------------------------------------------------------------


class TestAbstractEventOrganizerRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteEventOrganizerRepo()
        agg = _organizer_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_update_adds_to_seen(self):
        repo = _ConcreteEventOrganizerRepo()
        agg = _organizer_agg()
        repo.update(agg)
        assert agg in repo.seen

    def test_remove_adds_to_seen(self):
        repo = _ConcreteEventOrganizerRepo()
        agg = _organizer_agg()
        repo.remove(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _organizer_agg()
        repo = _ConcreteEventOrganizerRepo(return_value=agg)
        result = repo.get(1)
        assert result is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteEventOrganizerRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractEventPlaceRepository
# ---------------------------------------------------------------------------


class TestAbstractEventPlaceRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteEventPlaceRepo()
        agg = _place_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_update_adds_to_seen(self):
        repo = _ConcreteEventPlaceRepo()
        agg = _place_agg()
        repo.update(agg)
        assert agg in repo.seen

    def test_remove_adds_to_seen(self):
        repo = _ConcreteEventPlaceRepo()
        agg = _place_agg()
        repo.remove(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _place_agg()
        repo = _ConcreteEventPlaceRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteEventPlaceRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractEventReferenceRepository
# ---------------------------------------------------------------------------


class TestAbstractEventReferenceRepository:
    def test_get_by_event_id_returns_results(self):
        ref = _ref_agg()
        repo = _ConcreteEventReferenceRepo(return_values=[ref])
        results = repo.get_by_event_id(10)
        assert results == [ref]

    def test_get_by_event_id_adds_to_seen(self):
        ref1 = _ref_agg()
        ref2 = _ref_agg()
        repo = _ConcreteEventReferenceRepo(return_values=[ref1, ref2])
        repo.get_by_event_id(10)
        assert ref1 in repo.seen
        assert ref2 in repo.seen

    def test_get_by_event_id_empty(self):
        repo = _ConcreteEventReferenceRepo(return_values=[])
        results = repo.get_by_event_id(10)
        assert results == []
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractOrganizationRepository
# ---------------------------------------------------------------------------


class TestAbstractOrganizationRepository:
    def test_update_adds_to_seen(self):
        repo = _ConcreteOrganizationRepo()
        org = _org_agg()
        repo.update(org)
        assert org in repo.seen

    def test_get_with_result_adds_to_seen(self):
        org = _org_agg()
        repo = _ConcreteOrganizationRepo(return_value=org)
        assert repo.get(1) is org
        assert org in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteOrganizationRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractAppRepository
# ---------------------------------------------------------------------------


class TestAbstractAppRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteAppRepo()
        agg = _app_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_update_adds_to_seen(self):
        repo = _ConcreteAppRepo()
        agg = _app_agg()
        repo.update(agg)
        assert agg in repo.seen

    def test_remove_adds_to_seen(self):
        repo = _ConcreteAppRepo()
        agg = _app_agg()
        repo.remove(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _app_agg()
        repo = _ConcreteAppRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteAppRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractOrganizationAppInstallationRepository
# ---------------------------------------------------------------------------


class TestAbstractOrganizationAppInstallationRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteOrgAppInstallationRepo()
        agg = _installation_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_update_adds_to_seen(self):
        repo = _ConcreteOrgAppInstallationRepo()
        agg = _installation_agg()
        repo.update(agg)
        assert agg in repo.seen

    def test_remove_adds_to_seen(self):
        repo = _ConcreteOrgAppInstallationRepo()
        agg = _installation_agg()
        repo.remove(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _installation_agg()
        repo = _ConcreteOrgAppInstallationRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteOrgAppInstallationRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0

    def test_get_all_with_webhook_returns_matching_permissions(self):
        # Installation has both required permissions -> should be included
        inst_ok = _installation_agg(permissions=["read", "write", "admin"])
        repo = _ConcreteOrgAppInstallationRepo(all_with_webhook=[inst_ok])
        results = repo.get_all_with_webhook(
            admin_unit_id=2, permissions=["read", "write"], event_type="event.created"
        )
        assert inst_ok in results

    def test_get_all_with_webhook_excludes_missing_permissions(self):
        # Installation missing "write" permission -> should be excluded
        inst_no = _installation_agg(permissions=["read"])
        repo = _ConcreteOrgAppInstallationRepo(all_with_webhook=[inst_no])
        results = repo.get_all_with_webhook(
            admin_unit_id=2,
            permissions=["read", "write"],
            event_type="event.created",
        )
        assert inst_no not in results

    def test_get_all_with_webhook_empty_required_permissions_includes_all(self):
        inst = _installation_agg(permissions=[])
        repo = _ConcreteOrgAppInstallationRepo(all_with_webhook=[inst])
        results = repo.get_all_with_webhook(
            admin_unit_id=2, permissions=[], event_type="event.created"
        )
        assert inst in results


# ---------------------------------------------------------------------------
# AbstractOrganizationMemberRepository
# ---------------------------------------------------------------------------


class TestAbstractOrganizationMemberRepository:
    def test_get_all_with_permission_returns_results(self):
        member = _member_agg()
        repo = _ConcreteOrgMemberRepo(return_values=[member])
        results = repo.get_all_with_permission(admin_unit_id=2, permission="admin")
        assert results == [member]

    def test_get_all_with_permission_empty(self):
        repo = _ConcreteOrgMemberRepo(return_values=[])
        results = repo.get_all_with_permission(admin_unit_id=2, permission="admin")
        assert results == []


# ---------------------------------------------------------------------------
# AbstractWebhookDeliveryRepository
# ---------------------------------------------------------------------------


class TestAbstractWebhookDeliveryRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteWebhookDeliveryRepo()
        agg = _delivery_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _delivery_agg()
        repo = _ConcreteWebhookDeliveryRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteWebhookDeliveryRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractWebhookDeliveryAttemptRepository
# ---------------------------------------------------------------------------


class TestAbstractWebhookDeliveryAttemptRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteWebhookDeliveryAttemptRepo()
        agg = _attempt_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _attempt_agg()
        repo = _ConcreteWebhookDeliveryAttemptRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteWebhookDeliveryAttemptRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0


# ---------------------------------------------------------------------------
# AbstractWebhookEventRepository
# ---------------------------------------------------------------------------


class TestAbstractWebhookEventRepository:
    def test_add_adds_to_seen(self):
        repo = _ConcreteWebhookEventRepo()
        agg = _webhook_event_agg()
        repo.add(agg)
        assert agg in repo.seen

    def test_get_with_result_adds_to_seen(self):
        agg = _webhook_event_agg()
        repo = _ConcreteWebhookEventRepo(return_value=agg)
        assert repo.get(1) is agg
        assert agg in repo.seen

    def test_get_none_does_not_add_to_seen(self):
        repo = _ConcreteWebhookEventRepo(return_value=None)
        assert repo.get(1) is None
        assert len(repo.seen) == 0

    def test_delete_old_events_returns_count(self):
        repo = _ConcreteWebhookEventRepo(deleted_count=5)
        result = repo.delete_old_events(days=30)
        assert result == 5
