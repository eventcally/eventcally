"""The event visibility rule against a fake permission reader."""

import copy as _copy

import pytest

from project.application.read_models.event_visibility_read_model import (
    EventVisibilityReadModel,
)
from project.application.read_repositories.abstract_actor_permission_read_repository import (
    AbstractActorPermissionReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.actor_permission_policy import actor_can_use_planning
from project.application.services.event_visibility_service import EventVisibilityService
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus


class FakeReader(AbstractActorPermissionReadRepository):
    def __init__(
        self, admins=(), members=(), verified_members=(), installations=(), verified=()
    ):
        self.admins = set(admins)
        self.members = set(members)  # (admin_unit_id, user_id, permission)
        self.verified_members = set(verified_members)  # user ids
        self.installations = set(installations)  # (id, admin_unit_id, permission)
        self.verified_installations = set(verified)
        self.calls = []

    def is_platform_admin(self, user_id):
        return user_id in self.admins

    def member_has_permission(self, admin_unit_id, user_id, permission):
        self.calls.append((admin_unit_id, user_id, permission))
        return (admin_unit_id, user_id, permission) in self.members

    def installation_has_permission(self, app_installation_id, admin_unit_id, perm):
        return (app_installation_id, admin_unit_id, perm) in self.installations

    def user_email(self, user_id):  # pragma: no cover
        return None

    def is_member_of_verified_organization(self, user_id):
        return user_id in self.verified_members

    def installation_organization_is_verified(self, app_installation_id):
        return app_installation_id in self.verified_installations


def _service(reader):
    return EventVisibilityService(ActorAuthorizationService(reader))


def _visibility(status, verified=True, admin_unit_id=2):
    return EventVisibilityReadModel(
        event_id=1,
        public_status=status,
        admin_unit_id=admin_unit_id,
        admin_unit_is_verified=verified,
    )


PUBLISHED = EventPublicStatus.published
PLANNED = EventPublicStatus.planned
DRAFT = EventPublicStatus.draft


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=7)])
def test_published_events_of_verified_organizations_are_public(actor):
    assert _service(FakeReader()).can_read(actor, _visibility(PUBLISHED)) is True


@pytest.mark.parametrize("status", [PUBLISHED, PLANNED, DRAFT])
def test_unverified_organizations_need_the_permission(status):
    visibility = _visibility(status, verified=False)

    assert _service(FakeReader()).can_read(Actor(user_id=7), visibility) is False
    reader = FakeReader(members=[(2, 7, "events:read")])
    assert _service(reader).can_read(Actor(user_id=7), visibility) is True


def test_planned_events_need_the_right_to_plan():
    visibility = _visibility(PLANNED)

    assert _service(FakeReader()).can_read(Actor(user_id=7), visibility) is False
    assert _service(FakeReader()).can_read(None, visibility) is False
    assert (
        _service(FakeReader(verified_members=[7])).can_read(
            Actor(user_id=7), visibility
        )
        is True
    )
    assert (
        _service(FakeReader(verified=[5])).can_read(
            Actor(app_installation_id=5), visibility
        )
        is True
    )


def test_drafts_need_the_permission_even_for_planners():
    reader = FakeReader(verified_members=[7])
    visibility = _visibility(DRAFT)

    assert _service(reader).can_read(Actor(user_id=7), visibility) is False
    assert (
        _service(FakeReader(members=[(2, 7, "events:read")])).can_read(
            Actor(user_id=7), visibility
        )
        is True
    )
    assert (
        _service(FakeReader(admins=[7])).can_read(Actor(user_id=7), visibility) is True
    )
    assert (
        _service(FakeReader(installations=[(5, 2, "events:read")])).can_read(
            Actor(app_installation_id=5), visibility
        )
        is True
    )


def test_ensure_can_read_raises_for_a_stranger():
    service = _service(FakeReader())

    service.ensure_can_read(Actor(user_id=7), _visibility(PUBLISHED))
    with pytest.raises(UnauthorizedError):
        service.ensure_can_read(Actor(user_id=7), _visibility(DRAFT))


def test_planning_is_for_admins_verified_members_and_installations():
    reader = FakeReader(admins=[1], verified_members=[2], verified=[3])

    assert actor_can_use_planning(Actor(user_id=1), reader) is True
    assert actor_can_use_planning(Actor(user_id=2), reader) is True
    assert actor_can_use_planning(Actor(user_id=9), reader) is False
    assert actor_can_use_planning(Actor(app_installation_id=3), reader) is True
    assert actor_can_use_planning(Actor(app_installation_id=9), reader) is False
    assert actor_can_use_planning(Actor(), reader) is False
    assert actor_can_use_planning(None, reader) is False


class _Event:
    def __init__(self, admin_unit_id, internal_tags):
        self.admin_unit_id = admin_unit_id
        self.internal_tags = internal_tags

    def model_copy(self, update):
        copy = _copy.copy(self)
        copy.__dict__.update(update)
        return copy


def test_internal_tags_are_cleared_without_the_permission():
    reader = FakeReader(members=[(2, 7, "events:read")])
    events = [_Event(2, "a"), _Event(3, "b"), _Event(3, "c"), _Event(2, None)]

    result = _service(reader).redact_internal_tags(Actor(user_id=7), events)

    assert [e.internal_tags for e in result] == ["a", None, None, None]
    assert [c for c in reader.calls if c[0] == 3] == [(3, 7, "events:read")]  # cached


def test_the_detail_redacts_audit_and_reference_requests():
    class Detail(_Event):
        def __init__(self, tags="x"):
            super().__init__(2, tags)
            self.created_by_label = "who"
            self.updated_by_label = "who"
            self.reference_requests = ["request"]

    service = _service(FakeReader(members=[(2, 7, "events:read")]))
    redacted = service.redact_detail(Actor(user_id=7), Detail())

    assert redacted.internal_tags == "x"
    assert redacted.created_by_label == "who"
    assert redacted.reference_requests == []

    stranger = _service(FakeReader()).redact_detail(Actor(user_id=7), Detail())
    assert stranger.internal_tags is None
    assert stranger.created_by_label is None
    assert stranger.updated_by_label is None

    full = _service(
        FakeReader(
            members=[
                (2, 7, "events:read"),
                (2, 7, "outgoing_event_reference_requests:write"),
            ]
        )
    ).redact_detail(Actor(user_id=7), Detail())
    assert full.created_by_label == "who"
    assert full.reference_requests == ["request"]
