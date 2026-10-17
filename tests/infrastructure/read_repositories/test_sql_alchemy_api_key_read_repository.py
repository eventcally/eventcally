"""SqlAlchemyApiKeyReadRepository against the database."""

from datetime import datetime

import pytest
from sqlalchemy import text

from project.application.queries import (
    ApiKeySort,
    ListOrganizationApiKeysQuery,
    ListUserApiKeysQuery,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.api_key_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


@pytest.fixture
def keys(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    def insert(name, created_at, **owner):
        with app.app_context():
            from project.models import ApiKey

            api_key = ApiKey(name=name, **owner)
            api_key.generate_key()
            db.session.add(api_key)
            db.session.commit()
            db.session.execute(
                text("UPDATE apikey SET created_at = :created_at WHERE id = :id"),
                {"created_at": created_at, "id": api_key.id},
            )
            db.session.commit()
            return api_key.id

    return {
        "user_id": user_id,
        "admin_unit_id": admin_unit_id,
        "bravo": insert("bravo", datetime(2026, 1, 2), user_id=user_id),
        "alpha": insert("Alpha", datetime(2026, 1, 3), user_id=user_id),
        "org": insert("Org", datetime(2026, 1, 1), admin_unit_id=admin_unit_id),
    }


def test_user_list_sorts(read_repo, keys):
    by_name = read_repo("list", ListUserApiKeysQuery(user_id=keys["user_id"]))
    by_created = read_repo(
        "list",
        ListUserApiKeysQuery(user_id=keys["user_id"], sort=ApiKeySort.created_at_desc),
    )

    assert [item.name for item in by_name.items] == ["Alpha", "bravo"]
    assert [item.name for item in by_created.items] == ["Alpha", "bravo"]
    assert by_name.items[0].created_at == datetime(2026, 1, 3)


def test_organization_list_and_get(read_repo, keys):
    page = read_repo(
        "list", ListOrganizationApiKeysQuery(admin_unit_id=keys["admin_unit_id"])
    )

    assert [item.id for item in page.items] == [keys["org"]]
    org_key = read_repo("get", keys["org"])
    assert org_key.admin_unit_id == keys["admin_unit_id"]
    assert org_key.user_id is None
    assert org_key.rate_limit_value == "500/hour"
    assert read_repo("get", 4711) is None
    assert read_repo("organization_exists", keys["admin_unit_id"]) is True
    assert read_repo("organization_exists", 4711) is False


def test_get_audit_of_app_installation_actor(app, db, seeder, read_repo, keys):
    app_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=keys["admin_unit_id"]
    )
    installation_id = seeder.install_app(app_id, keys["admin_unit_id"])

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE apikey SET created_by_app_installation_id = :installation_id,"
                " updated_at = '2026-02-01' WHERE id = :id"
            ),
            {"installation_id": installation_id, "id": keys["org"]},
        )
        db.session.commit()

    audit = read_repo("get", keys["org"]).audit

    assert audit.created_by_label == "Mein Client"
    assert audit.updated_by_label is None
    assert audit.created_at == datetime(2026, 1, 1)
    assert audit.updated_at == datetime(2026, 2, 1)
