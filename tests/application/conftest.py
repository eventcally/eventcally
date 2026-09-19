"""Shared fake infrastructure for application-layer unit tests.

All tests in tests/application/ run without a real database.
"""

import pytest

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# Authorization helpers
#
# ACTOR is a user actor with a stable id; grant_permission() seeds it as an
# AdminUnitMember with a given permission for a given admin unit, for tests
# of handlers guarded by ensure_actor_has_permission_for_admin_unit.
# ---------------------------------------------------------------------------

ACTOR_USER_ID = 1
ACTOR = Actor(user_id=ACTOR_USER_ID)


def grant_permission(uow, admin_unit_id, permission, user_id=ACTOR_USER_ID):
    uow.organization_members.set_members_for(
        admin_unit_id,
        permission,
        [
            OrganisationMemberAggregate(
                id=admin_unit_id, admin_unit_id=admin_unit_id, user_id=user_id
            )
        ],
    )


# ---------------------------------------------------------------------------
# Generic in-memory repository
# ---------------------------------------------------------------------------


class FakeRepo:
    """Dict-based in-memory repo that mimics the AbstractRepository interface."""

    def __init__(self):
        self._store = {}
        self._next_id = 1
        self.seen = set()

    def add(self, obj):
        if not obj.id or obj.id < 0:
            obj.id = self._next_id
            self._next_id += 1
        else:
            if obj.id >= self._next_id:
                self._next_id = obj.id + 1
        self._store[obj.id] = obj
        self.seen.add(obj)

    def get(self, object_id):
        obj = self._store.get(object_id)
        if obj:
            self.seen.add(obj)
        return obj

    def update(self, obj):
        self._store[obj.id] = obj
        self.seen.add(obj)

    def remove(self, obj):
        self._store.pop(obj.id, None)
        self.seen.add(obj)


# ---------------------------------------------------------------------------
# Specialised repositories
# ---------------------------------------------------------------------------


class FakeWebhookEventRepo(FakeRepo):
    def __init__(self):
        super().__init__()
        self.deleted_days = None
        self.delete_count = 0

    def delete_old_events(self, days: int) -> int:
        self.deleted_days = days
        return self.delete_count


class FakeOrganizationMemberRepo(FakeRepo):
    def __init__(self):
        super().__init__()
        self._members_by_unit = {}

    def get_all_with_permission(self, admin_unit_id, permission):
        return self._members_by_unit.get(admin_unit_id, [])

    def set_members_for(self, admin_unit_id, permission, members):
        """Test helper: seed members for a given admin_unit_id."""
        self._members_by_unit[admin_unit_id] = members

    def get_by_admin_unit_and_user(self, admin_unit_id, user_id):
        for obj in self._store.values():
            if obj.admin_unit_id == admin_unit_id and obj.user_id == user_id:
                self.seen.add(obj)
                return obj
        return None


class FakeUserRepo(FakeRepo):
    def __init__(self):
        super().__init__()

    def get_all_with_ids(self, user_ids):
        return [self._store[uid] for uid in user_ids if uid in self._store]

    def reset_tos_accepted_for_all(self):
        count = 0
        for user in self._store.values():
            if user.tos_accepted_at is not None:
                user.tos_accepted_at = None
                count += 1
        return count


class FakeEventReferenceRepo(FakeRepo):
    def __init__(self):
        super().__init__()
        self._references_by_event = {}

    def get_by_event_id(self, event_id):
        return self._references_by_event.get(event_id, [])

    def get_by_event_and_admin_unit(self, event_id, admin_unit_id):
        for obj in self._store.values():
            if obj.event_id == event_id and obj.admin_unit_id == admin_unit_id:
                self.seen.add(obj)
                return obj
        return None


class FakeOrganizationRelationRepo(FakeRepo):
    def get_by_source_and_target(self, source_admin_unit_id, target_admin_unit_id):
        for obj in self._store.values():
            if (
                obj.source_admin_unit_id == source_admin_unit_id
                and obj.target_admin_unit_id == target_admin_unit_id
            ):
                self.seen.add(obj)
                return obj
        return None


class FakeOrgAppInstallationRepo(FakeRepo):
    def __init__(self):
        super().__init__()
        self._webhook_installations = []

    def get_all_with_webhook(self, admin_unit_id, permissions, event_type):
        return list(self._webhook_installations)


class FakeApiKeyRepo(FakeRepo):
    def count_for_owner(self, user_id, admin_unit_id):
        return sum(
            1
            for obj in self._store.values()
            if obj.user_id == user_id and obj.admin_unit_id == admin_unit_id
        )


class FakeSettingsRepo:
    """Singleton-shaped fake — get() takes no id, mirrors the Settings table
    having exactly one row."""

    def __init__(self):
        self._store = None
        self.seen = set()

    def add(self, settings):
        if not settings.id or settings.id < 0:
            settings.id = 1
        self._store = settings
        self.seen.add(settings)

    def update(self, settings):
        self._store = settings
        self.seen.add(settings)

    def get(self):
        if self._store:
            self.seen.add(self._store)
        return self._store


# ---------------------------------------------------------------------------
# Fake Unit of Work
# ---------------------------------------------------------------------------


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events = FakeRepo()
        self.event_organizers = FakeRepo()
        self.event_references = FakeEventReferenceRepo()
        self.event_reference_requests = FakeRepo()
        self.event_places = FakeRepo()
        self.organizations = FakeRepo()
        self.organization_relations = FakeOrganizationRelationRepo()
        self.organization_verification_requests = FakeRepo()
        self.webhook_events = FakeWebhookEventRepo()
        self.webhook_deliveries = FakeRepo()
        self.webhook_delivery_attempts = FakeRepo()
        self.apps = FakeRepo()
        self.organization_app_installations = FakeOrgAppInstallationRepo()
        self.organization_members = FakeOrganizationMemberRepo()
        self.users = FakeUserRepo()
        self.custom_widgets = FakeRepo()
        self.api_keys = FakeApiKeyRepo()
        self.app_keys = FakeRepo()
        self.oauth2_clients = FakeRepo()
        self.oauth2_tokens = FakeRepo()
        self.organization_invitations = FakeRepo()
        self.member_invitations = FakeRepo()
        self.settings = FakeSettingsRepo()
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


# ---------------------------------------------------------------------------
# Service stubs
# ---------------------------------------------------------------------------


class FakeEmailService:
    def __init__(self):
        self.calls = []

    def send_template_mails_to_users_async(self, users, template, **context):
        self.calls.append({"users": users, "template": template, "context": context})

    def send_template_mail_to_address_async(self, email, template, **context):
        self.calls.append({"email": email, "template": template, "context": context})


class FakeEventDispatcher:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, event):
        self.dispatched.append(event)


class FakeCommandDispatcher:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, command):
        self.dispatched.append(command)


class FakeAppContextProvider:
    def __init__(self, actor=None):
        self._actor = actor or Actor()

    def get_current_actor(self):
        return self._actor


class FakeApiKeyGenerator:
    def __init__(self, key="plaintext-key", key_hash="hashed-key"):
        self.key = key
        self.key_hash = key_hash

    def generate(self):
        return self.key, self.key_hash


class FakeAppKeyGenerator:
    def __init__(
        self,
        checksum="fake-checksum",
        kid="fake-kid",
        public_key="fake-public-key",
        private_pem="fake-private-pem",
    ):
        self.checksum = checksum
        self.kid = kid
        self.public_key = public_key
        self.private_pem = private_pem

    def generate(self):
        return self.checksum, self.kid, self.public_key, self.private_pem


class FakeOAuth2ClientCredentialsGenerator:
    def __init__(self, client_id="fake-client-id", client_secret="fake-client-secret"):
        self.client_id = client_id
        self.client_secret = client_secret

    def generate(self):
        return self.client_id, self.client_secret


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def actor():
    return Actor()


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def email_service():
    return FakeEmailService()


@pytest.fixture
def event_dispatcher():
    return FakeEventDispatcher()


@pytest.fixture
def command_dispatcher():
    return FakeCommandDispatcher()
