import pytest


def test_shell(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get("/admin/users")

    utils.assert_response_ok(response)
    assert b'id="app"' in response.data
    assert b'"bffBase": "/bff"' in response.data
    assert b"ext/bootstrap.5.3.3.min.css" in response.data


def test_shell_root(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get("/admin/")

    utils.assert_response_ok(response)


def test_shell_anonymous_redirects_to_login(client, utils):
    response = client.get("/admin/users")

    utils.assert_response_redirect_to_login(response, "/admin/users")


def test_shell_forbidden_for_non_admin(client, seeder, utils):
    seeder.create_user()
    utils.login()

    response = client.get("/admin/users")

    utils.assert_response_forbidden(response)


def test_main_menu_contains_docs_link(app, client, seeder, utils):
    app.config["DOCS_URL"] = "https://docs.example.org"
    seeder.create_user(admin=True)
    utils.login()

    response = client.get("/admin/")

    assert b'href="https://docs.example.org"' in response.data


def test_shell_shows_manage_toolbar(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(True)
    utils.get_endpoint_ok("manage_admin_unit.events", id=admin_unit_id)

    response = client.get("/admin/users")

    utils.assert_response_ok(response)
    assert b"navbarAdminUnitEventsDropdown" in response.data
    assert b'data-bs-toggle="dropdown"' in response.data
    assert b"Meine Crew" in response.data


def test_admin_without_slash_redirects(client):
    response = client.get("/admin")

    assert response.status_code == 308
    assert response.headers["Location"].endswith("/admin/")


def test_unknown_path_serves_shell(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get("/admin/does-not-exist")

    utils.assert_response_ok(response)
    assert b'id="app"' in response.data


@pytest.mark.parametrize(
    "path",
    ["/admin/flask-admin/", "/admin/flask-admin/flask_admin_authmodelview_user/"],
)
def test_flask_admin_is_not_shadowed(client, seeder, utils, path):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get(path)

    utils.assert_response_ok(response)
    assert b'id="app"' not in response.data
    assert b"flask-admin" in response.data.lower()


def test_admin_next_redirects_permanently(client):
    response = client.get("/admin-next/users?page=2")

    assert response.status_code == 301
    assert response.headers["Location"].endswith("/admin/users?page=2")

    response = client.get("/admin-next/")

    assert response.status_code == 301
    assert response.headers["Location"].endswith("/admin/")


def test_main_menu_links_to_admin(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get(utils.get_url("main.home"))

    assert b'href="/admin/"' in response.data
