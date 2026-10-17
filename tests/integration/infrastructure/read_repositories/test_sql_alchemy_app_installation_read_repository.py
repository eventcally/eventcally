"""SqlAlchemyAppInstallationReadRepository against the database."""

import pytest

from project.application.queries import ListAppInstallationsQuery


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.app_installation_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_installations_and_installable_app(read_repo, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Andere Crew")
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=other_admin_unit_id)
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)

    page = read_repo("list", ListAppInstallationsQuery(admin_unit_id=admin_unit_id))
    installation = read_repo("get", installation_id)
    installable = read_repo("get_installable_app", app_id)

    assert [item.id for item in page.items] == [installation_id]
    assert installation.admin_unit_id == admin_unit_id
    assert installation.oauth2_client.client_name == "Mein Client"
    assert installation.permissions
    assert installation.created_at is not None
    assert installable.app_permissions
    assert read_repo("get_installable_app", client_id) is None
    assert read_repo("get", 4711) is None
    assert read_repo("organization_exists", admin_unit_id) is True


def test_installations_of_app_for_user(app, db, seeder):
    from project.application.queries import ListUserAppInstallationsQuery

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_owner_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Andere Crew")
    foreign_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Fremde Crew")

    from project.cli.seed_helpers import (
        add_user_to_admin_unit_with_roles,
        get_admin_unit_by_id,
    )
    from project.user_datastore import get_user

    with app.app_context():
        add_user_to_admin_unit_with_roles(
            get_user(user_id),
            get_admin_unit_by_id(other_admin_unit_id),
            ["event_verifier"],
        )
        db.session.commit()

    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    own_id = seeder.install_app(app_id, admin_unit_id)
    other_id = seeder.install_app(app_id, other_admin_unit_id)
    seeder.install_app(app_id, foreign_admin_unit_id)

    with app.app_context():
        repo = app.container.read_repos.app_installation_read_repo()

        with app.container.infrastructure.read_session_scope():
            page = repo.list_for_user(
                ListUserAppInstallationsQuery(user_id=user_id, app_id=app_id)
            )
            admin_only = repo.list_for_user(
                ListUserAppInstallationsQuery(
                    user_id=user_id, app_id=app_id, admin_only=True
                )
            )

    assert [item.id for item in page.items] == [own_id, other_id]
    assert page.items[0].membership.is_admin is True
    assert page.items[1].membership.is_admin is False
    assert page.items[1].admin_unit.name == "Andere Crew"
    assert [item.id for item in admin_only.items] == [own_id]
