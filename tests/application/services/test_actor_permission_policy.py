"""The single authorization rule, against a fake permission reader."""

from project.application.read_repositories.abstract_actor_permission_read_repository import (
    AbstractActorPermissionReadRepository,
)
from project.application.services.actor_permission_policy import (
    actor_has_permission_for_admin_unit,
)
from project.domain.models.entities.actor import Actor

PERMISSION = "organization_invitations:read"


class FakeActorPermissionReader(AbstractActorPermissionReadRepository):
    def __init__(self, admins=(), members=(), installations=(), emails=None):
        self.emails = dict(emails or {})  # user_id -> email
        self.admins = set(admins)
        self.members = set(members)  # (admin_unit_id, user_id, permission)
        self.installations = set(installations)  # (id, admin_unit_id, permission)
        self.installation_lookups = 0

    def is_platform_admin(self, user_id):
        return user_id in self.admins

    def user_email(self, user_id):
        return self.emails.get(user_id)

    def member_has_permission(self, admin_unit_id, user_id, permission):
        return (admin_unit_id, user_id, permission) in self.members

    def installation_has_permission(
        self, app_installation_id, admin_unit_id, permission
    ):
        self.installation_lookups += 1
        return (app_installation_id, admin_unit_id, permission) in self.installations


def _check(actor, reader):
    return actor_has_permission_for_admin_unit(actor, 2, PERMISSION, reader)


def test_none_actor_is_refused():
    assert _check(None, FakeActorPermissionReader()) is False


def test_empty_actor_is_refused():
    assert _check(Actor(), FakeActorPermissionReader()) is False


def test_platform_admin_without_membership_is_permitted():
    assert _check(Actor(user_id=7), FakeActorPermissionReader(admins=[7])) is True


def test_member_with_permission_is_permitted():
    reader = FakeActorPermissionReader(members=[(2, 7, PERMISSION)])

    assert _check(Actor(user_id=7), reader) is True


def test_member_without_permission_is_refused():
    reader = FakeActorPermissionReader(members=[(2, 7, "other:read")])

    assert _check(Actor(user_id=7), reader) is False


def test_member_of_another_organization_is_refused():
    reader = FakeActorPermissionReader(members=[(3, 7, PERMISSION)])

    assert _check(Actor(user_id=7), reader) is False


def test_user_actor_never_consults_the_installation_branch():
    reader = FakeActorPermissionReader(installations=[(5, 2, PERMISSION)])

    assert _check(Actor(user_id=7, app_installation_id=5), reader) is False
    assert reader.installation_lookups == 0


def test_installation_of_the_organization_with_permission_is_permitted():
    reader = FakeActorPermissionReader(installations=[(5, 2, PERMISSION)])

    assert _check(Actor(app_installation_id=5), reader) is True


def test_installation_without_permission_is_refused():
    reader = FakeActorPermissionReader(installations=[(5, 2, "other:read")])

    assert _check(Actor(app_installation_id=5), reader) is False


def test_installation_of_another_organization_is_refused():
    reader = FakeActorPermissionReader(installations=[(5, 3, PERMISSION)])

    assert _check(Actor(app_installation_id=5), reader) is False
