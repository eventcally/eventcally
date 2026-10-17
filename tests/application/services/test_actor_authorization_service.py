import pytest

from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.application.services.test_actor_permission_policy import (
    PERMISSION,
    FakeActorPermissionReader,
)


def test_has_permission_for_admin_unit_delegates_to_the_policy():
    service = ActorAuthorizationService(
        FakeActorPermissionReader(members=[(2, 7, PERMISSION)])
    )

    assert service.has_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION)
    assert not service.has_permission_for_admin_unit(Actor(user_id=8), 2, PERMISSION)


def test_ensure_passes_when_permitted():
    service = ActorAuthorizationService(
        FakeActorPermissionReader(members=[(2, 7, PERMISSION)])
    )

    service.ensure_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION)


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=8)])
def test_ensure_raises_with_message_when_refused(actor):
    service = ActorAuthorizationService(FakeActorPermissionReader())

    with pytest.raises(UnauthorizedError) as exc_info:
        service.ensure_permission_for_admin_unit(actor, 2, PERMISSION)

    assert (
        exc_info.value.message
        == f"Actor is not permitted to perform '{PERMISSION}' for admin unit 2."
    )


def test_ensure_is_user_passes_for_the_user():
    ActorAuthorizationService(FakeActorPermissionReader()).ensure_is_user(
        Actor(user_id=7), 7
    )


@pytest.mark.parametrize(
    "actor", [None, Actor(), Actor(user_id=8), Actor(app_installation_id=7)]
)
def test_ensure_is_user_raises_for_anyone_else(actor):
    with pytest.raises(UnauthorizedError):
        ActorAuthorizationService(FakeActorPermissionReader()).ensure_is_user(actor, 7)


def test_ensure_is_platform_admin_passes_for_admin():
    service = ActorAuthorizationService(FakeActorPermissionReader(admins=[7]))

    service.ensure_is_platform_admin(Actor(user_id=7))


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=8)])
def test_ensure_is_platform_admin_raises_for_non_admins(actor):
    service = ActorAuthorizationService(FakeActorPermissionReader(admins=[7]))

    with pytest.raises(UnauthorizedError):
        service.ensure_is_platform_admin(actor)


@pytest.mark.parametrize(
    "actor, email, expected",
    [
        (Actor(user_id=7), "Invited@Test.de", True),
        (Actor(user_id=7), "other@test.de", False),
        (Actor(user_id=8), "invited@test.de", False),
        (Actor(), "invited@test.de", False),
        (None, "invited@test.de", False),
        (Actor(user_id=7), None, False),
    ],
)
def test_is_recipient(actor, email, expected):
    service = ActorAuthorizationService(
        FakeActorPermissionReader(emails={7: "invited@test.de"})
    )

    assert service.is_recipient(actor, email) is expected

    if expected:
        service.ensure_is_recipient(actor, email)
    else:
        with pytest.raises(UnauthorizedError):
            service.ensure_is_recipient(actor, email)
