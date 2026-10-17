"""SqlAlchemyOAuth2ClientReadRepository against the database."""

import pytest

from project.application.queries import (
    ListAppsQuery,
    ListOrganizationOAuth2ClientsQuery,
    ListUserOAuth2ClientsQuery,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.oauth2_client_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


@pytest.fixture
def clients(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    ids = {
        "user": seeder.insert_default_oauth2_client(user_id),
        "org": seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id),
        "app": seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id),
    }

    with app.app_context():
        from project.models import OAuth2Client, Webhook

        client = db.session.get(OAuth2Client, ids["app"])
        client.homepage_url = "https://example.com"
        client.webhook = Webhook(
            url="https://hook.example.com", event_types=["app.installed"]
        )
        db.session.commit()

    return {"user_id": user_id, "admin_unit_id": admin_unit_id, **ids}


def test_lists_split_by_owner_and_app(read_repo, clients):
    user_page = read_repo(
        "list", ListUserOAuth2ClientsQuery(user_id=clients["user_id"])
    )
    org_page = read_repo(
        "list",
        ListOrganizationOAuth2ClientsQuery(admin_unit_id=clients["admin_unit_id"]),
    )
    app_page = read_repo("list", ListAppsQuery(admin_unit_id=clients["admin_unit_id"]))

    assert [item.id for item in user_page.items] == [clients["user"]]
    assert [item.id for item in org_page.items] == [clients["org"]]
    assert [item.id for item in app_page.items] == [clients["app"]]
    assert app_page.items[0].webhook.url == "https://hook.example.com"


def test_get(read_repo, clients):
    client = read_repo("get", clients["user"])

    assert client.client_name == "Mein Client"
    assert client.user_id == clients["user_id"]
    assert client.redirect_uris[0].endswith("/oauth2-redirect.html")
    assert "openid" in client.scope.split(" ")
    assert client.client_id
    assert read_repo("get", 4711) is None


def test_get_app(read_repo, clients):
    app_model = read_repo("get_app", clients["app"])

    assert app_model.homepage_url == "https://example.com"
    assert app_model.webhook.event_types == ["app.installed"]
    assert app_model.app_permissions
    assert read_repo("get_app", clients["org"]) is None
    assert read_repo("organization_exists", clients["admin_unit_id"]) is True
    assert read_repo("organization_exists", 4711) is False
