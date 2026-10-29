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


def test_main_menu_links_to_admin(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = client.get(utils.get_url("main.home"))

    assert b'href="/admin/"' in response.data


def _flask_admin_view(app, endpoint):
    return next(
        v
        for admin in app.extensions["admin"]
        for v in admin._views
        if v.endpoint == endpoint
    )


def test_flask_admin_hides_collection_relations(app):
    view = _flask_admin_view(app, "flask_admin_authmodelview_adminunitmember")
    columns = [name for name, _ in view._list_columns]

    assert "user" in columns
    assert "roles" not in columns
    for form_class in (view._create_form_class, view._edit_form_class):
        assert hasattr(form_class, "user")
        assert not hasattr(form_class, "roles")

    view = _flask_admin_view(app, "flask_admin_authmodelview_user")
    assert "api_keys" not in [name for name, _ in view._list_columns]
    assert not hasattr(view._create_form_class, "api_keys")


def test_flask_admin_custom_form_columns_keep_collection_relations(app):
    view = _flask_admin_view(app, "flask_admin_userview_user")

    assert hasattr(view._edit_form_class, "roles")


def test_flask_admin_edit_form_with_unique_column(client, seeder, utils):
    user_id = seeder.create_user(admin=True)
    utils.login()

    response = client.get(
        f"/admin/flask-admin/flask_admin_authmodelview_user/edit/?id={user_id}"
    )

    utils.assert_response_ok(response)


@pytest.mark.parametrize(
    "endpoint, model_name",
    [
        ("flask_admin_organizationview_adminunit", "AdminUnit"),
        ("flask_admin_userview_user", "User"),
    ],
)
def test_flask_admin_custom_views_show_and_edit_max_api_keys(
    app, db, client, seeder, utils, endpoint, model_name
):
    from project.infrastructure import models

    user_id, admin_unit_id = seeder.setup_base(admin=True)
    model = getattr(models, model_name)
    object_id = admin_unit_id if model_name == "AdminUnit" else user_id
    base_url = f"/admin/flask-admin/{endpoint}/"

    response = utils.get_ok(base_url)
    assert b"Max Api Keys" in response.data

    response = utils.get_ok(f"{base_url}details/?id={object_id}")
    assert b"Max Api Keys" in response.data

    edit_url = f"{base_url}edit/?id={object_id}"
    response = utils.get_ok(edit_url)
    assert b'name="max_api_keys"' in response.data

    response = utils.post_form(edit_url, response, {"max_api_keys": "5"})
    assert response.status_code == 302

    with app.app_context():
        saved = db.session.get(model, object_id)
        assert saved.max_api_keys == 5
        if model_name == "User":
            assert saved.active
            assert [role.name for role in saved.roles] == ["admin"]
        else:
            assert saved.can_invite_other
