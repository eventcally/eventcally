"""Unit tests for the actor-based authorization pilot.

Deliberately keyed off `Actor` (`user_id` xor `app_installation_id`) rather
than Flask-Login's `current_user` / Authlib's `current_token`, so the same
check works for a command dispatched outside an HTTP request.
"""

import pytest

from project.application.command_handlers.authorization_utils import (
    ensure_actor_has_permission_for_admin_unit,
    has_actor_permission_for_admin_unit,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor

PERMISSION = "incoming_organization_verification_requests:write"


class TestHasActorPermissionForAdminUnit:
    def test_true_when_user_is_platform_admin_without_membership(self, uow):
        uow.users.add(
            UserAggregate(
                id=7, email="admin@test.de", locale=None, is_platform_admin=True
            )
        )

        assert (
            has_actor_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION, uow)
            is True
        )

    def test_false_when_user_exists_but_is_not_platform_admin_or_member(self, uow):
        uow.users.add(
            UserAggregate(
                id=7, email="user@test.de", locale=None, is_platform_admin=False
            )
        )

        assert (
            has_actor_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION, uow)
            is False
        )

    def test_true_when_user_is_member_with_permission(self, uow):
        uow.organization_members.set_members_for(
            2,
            PERMISSION,
            [OrganisationMemberAggregate(id=1, admin_unit_id=2, user_id=7)],
        )

        assert (
            has_actor_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION, uow)
            is True
        )

    def test_false_when_user_is_not_a_member(self, uow):
        uow.organization_members.set_members_for(
            2,
            PERMISSION,
            [OrganisationMemberAggregate(id=1, admin_unit_id=2, user_id=7)],
        )

        assert (
            has_actor_permission_for_admin_unit(Actor(user_id=8), 2, PERMISSION, uow)
            is False
        )

    def test_false_when_member_list_is_empty(self, uow):
        assert (
            has_actor_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION, uow)
            is False
        )

    def test_true_when_app_installation_has_permission(self, uow):
        uow.organization_app_installations.add(
            OrganisationAppInstallationAggregate(
                id=5, admin_unit_id=2, app_id=1, permissions={PERMISSION}
            )
        )

        assert (
            has_actor_permission_for_admin_unit(
                Actor(app_installation_id=5), 2, PERMISSION, uow
            )
            is True
        )

    def test_false_when_app_installation_missing_permission(self, uow):
        uow.organization_app_installations.add(
            OrganisationAppInstallationAggregate(
                id=5, admin_unit_id=2, app_id=1, permissions=set()
            )
        )

        assert (
            has_actor_permission_for_admin_unit(
                Actor(app_installation_id=5), 2, PERMISSION, uow
            )
            is False
        )

    def test_false_when_app_installation_belongs_to_different_admin_unit(self, uow):
        uow.organization_app_installations.add(
            OrganisationAppInstallationAggregate(
                id=5, admin_unit_id=99, app_id=1, permissions={PERMISSION}
            )
        )

        assert (
            has_actor_permission_for_admin_unit(
                Actor(app_installation_id=5), 2, PERMISSION, uow
            )
            is False
        )

    def test_false_when_app_installation_not_found(self, uow):
        assert (
            has_actor_permission_for_admin_unit(
                Actor(app_installation_id=999), 2, PERMISSION, uow
            )
            is False
        )

    def test_false_when_actor_has_neither_user_nor_app_installation(self, uow):
        assert has_actor_permission_for_admin_unit(Actor(), 2, PERMISSION, uow) is False


class TestEnsureActorHasPermissionForAdminUnit:
    def test_passes_silently_when_permitted(self, uow):
        uow.organization_members.set_members_for(
            2,
            PERMISSION,
            [OrganisationMemberAggregate(id=1, admin_unit_id=2, user_id=7)],
        )

        ensure_actor_has_permission_for_admin_unit(Actor(user_id=7), 2, PERMISSION, uow)

    def test_raises_unauthorized_error_when_not_permitted(self, uow):
        with pytest.raises(UnauthorizedError):
            ensure_actor_has_permission_for_admin_unit(
                Actor(user_id=7), 2, PERMISSION, uow
            )
