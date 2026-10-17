"""SqlAlchemyActorPermissionReadRepository against the database, on the read session,
and its parity with the unit-of-work answers commands use."""

import pytest

from project.application.command_handlers.authorization_utils import (
    has_actor_permission_for_admin_unit,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.sql_alchemy_unit_of_work import SqlAlchemyUnitOfWork

PERMISSION = "organization_invitations:read"


@pytest.fixture
def scenario(app, db, seeder):
    """Two organizations, members with different roles, a platform admin and
    app installations with and without the permission."""
    owner_id, admin_unit_id = seeder.setup_base(log_in=False)
    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], email="verifier@test.de"
    )
    platform_admin_id = seeder.create_user(email="platform@test.de", admin=True)

    with app.app_context():
        from project.models import User

        verifier_id = User.query.filter_by(email="verifier@test.de").one().id
        other_owner_id = User.query.filter_by(email="other@test.de").one().id

    client_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    with_permission_id = seeder.install_app(client_id, admin_unit_id)
    other_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id
    )
    other_org_installation_id = seeder.install_app(other_client_id, other_admin_unit_id)
    no_permission_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id, app_permissions=["organization_invitations:write"]
    )
    without_permission_id = seeder.install_app(no_permission_client_id, admin_unit_id)

    return {
        "admin_unit_id": admin_unit_id,
        "other_admin_unit_id": other_admin_unit_id,
        "owner_id": owner_id,
        "other_owner_id": other_owner_id,
        "verifier_id": verifier_id,
        "platform_admin_id": platform_admin_id,
        "with_permission_id": with_permission_id,
        "without_permission_id": without_permission_id,
        "other_org_installation_id": other_org_installation_id,
    }


def _read(app, fn):
    with app.app_context():
        repo = app.container.read_repos.actor_permission_read_repo()

        with app.container.infrastructure.read_session_scope():
            return fn(repo)


def test_is_platform_admin(app, scenario):
    assert _read(app, lambda r: r.is_platform_admin(scenario["platform_admin_id"]))
    assert not _read(app, lambda r: r.is_platform_admin(scenario["owner_id"]))
    assert not _read(app, lambda r: r.is_platform_admin(4711))


def test_member_has_permission(app, scenario):
    org = scenario["admin_unit_id"]

    assert _read(
        app, lambda r: r.member_has_permission(org, scenario["owner_id"], PERMISSION)
    )


def test_member_role_without_the_permission_is_refused(app, scenario):
    org = scenario["admin_unit_id"]

    assert not _read(
        app, lambda r: r.member_has_permission(org, scenario["verifier_id"], PERMISSION)
    )


def test_member_of_another_organization_is_refused(app, scenario):
    org = scenario["admin_unit_id"]

    assert not _read(
        app,
        lambda r: r.member_has_permission(org, scenario["other_owner_id"], PERMISSION),
    )
    assert not _read(app, lambda r: r.member_has_permission(org, 4711, PERMISSION))


def test_installation_has_permission(app, scenario):
    org = scenario["admin_unit_id"]

    assert _read(
        app,
        lambda r: r.installation_has_permission(
            scenario["with_permission_id"], org, PERMISSION
        ),
    )
    assert not _read(
        app,
        lambda r: r.installation_has_permission(
            scenario["without_permission_id"], org, PERMISSION
        ),
    )
    assert not _read(
        app,
        lambda r: r.installation_has_permission(
            scenario["other_org_installation_id"], org, PERMISSION
        ),
    )
    assert not _read(
        app, lambda r: r.installation_has_permission(4711, org, PERMISSION)
    )


def _actors(s):
    return {
        "owner": Actor(user_id=s["owner_id"]),
        "verifier": Actor(user_id=s["verifier_id"]),
        "platform_admin": Actor(user_id=s["platform_admin_id"]),
        "other_org_owner": Actor(user_id=s["other_owner_id"]),
        "unknown_user": Actor(user_id=4711),
        "installation_with": Actor(app_installation_id=s["with_permission_id"]),
        "installation_without": Actor(app_installation_id=s["without_permission_id"]),
        "installation_other_org": Actor(
            app_installation_id=s["other_org_installation_id"]
        ),
        "unknown_installation": Actor(app_installation_id=4711),
        "user_with_installation_id": Actor(
            user_id=s["verifier_id"], app_installation_id=s["with_permission_id"]
        ),
        "empty": Actor(),
    }


def test_command_and_query_paths_agree_on_every_scenario(app, scenario):
    expected = {
        "owner": True,
        "verifier": False,
        "platform_admin": True,
        "other_org_owner": False,
        "unknown_user": False,
        "installation_with": True,
        "installation_without": False,
        "installation_other_org": False,
        "unknown_installation": False,
        "user_with_installation_id": False,
        "empty": False,
    }
    actors = _actors(scenario)
    assert actors.keys() == expected.keys()

    with app.app_context():
        uow = SqlAlchemyUnitOfWork(app.container.infrastructure.session_factory())
        command_side = {
            name: has_actor_permission_for_admin_unit(
                actor, scenario["admin_unit_id"], PERMISSION, uow
            )
            for name, actor in actors.items()
        }

        authz = ActorAuthorizationService(
            app.container.read_repos.actor_permission_read_repo()
        )

        with app.container.infrastructure.read_session_scope():
            query_side = {
                name: authz.has_permission_for_admin_unit(
                    actor, scenario["admin_unit_id"], PERMISSION
                )
                for name, actor in actors.items()
            }

    assert command_side == expected
    assert query_side == expected


def test_user_email(app, scenario):
    assert _read(app, lambda r: r.user_email(scenario["owner_id"])) == "test@test.de"
    assert _read(app, lambda r: r.user_email(4711)) is None


def test_unit_of_work_reader_user_email(app, scenario):
    from project.application.command_handlers.authorization_utils import (
        _UnitOfWorkActorPermissionReader,
    )

    with app.app_context():
        uow = SqlAlchemyUnitOfWork(app.container.infrastructure.session_factory())
        reader = _UnitOfWorkActorPermissionReader(uow)

        assert reader.user_email(scenario["owner_id"]) == "test@test.de"
        assert reader.user_email(4711) is None


def test_planning_facts_follow_the_verification_of_the_organization(
    app, db, seeder, scenario
):
    unverified_user_id, unverified_admin_unit_id = seeder.setup_base(
        email="unverified@test.de",
        name="Unverified Crew",
        log_in=False,
        admin_unit_verified=False,
    )
    client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=unverified_admin_unit_id
    )
    unverified_installation_id = seeder.install_app(client_id, unverified_admin_unit_id)

    assert _read(
        app, lambda r: r.is_member_of_verified_organization(scenario["owner_id"])
    )
    assert not _read(
        app, lambda r: r.is_member_of_verified_organization(unverified_user_id)
    )
    assert not _read(app, lambda r: r.is_member_of_verified_organization(4711))
    assert _read(
        app,
        lambda r: r.installation_organization_is_verified(
            scenario["with_permission_id"]
        ),
    )
    assert not _read(
        app,
        lambda r: r.installation_organization_is_verified(unverified_installation_id),
    )
    assert not _read(app, lambda r: r.installation_organization_is_verified(4711))

    service = app.container.cqrs.actor_authorization_service()
    with app.app_context():
        assert service.can_use_planning(Actor(user_id=scenario["owner_id"])) is True
        assert service.can_use_planning(Actor(user_id=unverified_user_id)) is False
