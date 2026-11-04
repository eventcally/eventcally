import pytest

BASE_URL = "/bff/manage/organizations/{}/oauth2-clients"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/oauth2_clients")


def _client_values(app, db, client_id):
    from project.infrastructure.models import OAuth2Client

    with app.app_context():
        client = db.session.get(OAuth2Client, client_id)
        return client and (client.client_name, client.scope, client.redirect_uris)


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


@pytest.fixture
def setup(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    _shell(utils, admin_unit_id)
    return user_id, admin_unit_id, client_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)
    body = dict(client_name="x")

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/form").status_code == 401
    assert utils.get_json(f"{base}/1").status_code == 401
    assert utils.post_json(base, body).status_code == 401
    assert utils.put_json(f"{base}/1", body).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict(name="x")).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)
    body = dict(client_name="x")

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/form").status_code == 403
    assert utils.get_json(f"{base}/{client_id}").status_code == 403
    assert utils.post_json(base, body).status_code == 403
    assert utils.put_json(f"{base}/{client_id}", body).status_code == 403
    assert (
        utils.post_json(f"{base}/{client_id}/delete", dict(name="x")).status_code == 403
    )


def test_writes_require_csrf(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.post_json(base, dict(client_name="x")).status_code == 400
    assert (
        utils.put_json(f"{base}/{client_id}", dict(client_name="x")).status_code == 400
    )
    assert (
        utils.post_json(f"{base}/{client_id}/delete", dict(name="x")).status_code == 400
    )


def test_clients_of_others_are_404(client, app, db, seeder, utils, setup):
    user_id, admin_unit_id, _ = setup
    other_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id = seeder.insert_default_oauth2_client(admin_unit_id=other_unit_id)
    own_user_client_id = seeder.insert_default_oauth2_client(user_id=user_id)
    base = BASE_URL.format(admin_unit_id)

    for client_id in (foreign_id, own_user_client_id, 4711):
        assert utils.get_json(f"{base}/{client_id}").status_code == 404
        assert (
            utils.put_json(f"{base}/{client_id}", dict(client_name="Neu")).status_code
            == 404
        )
        assert (
            utils.post_json(
                f"{base}/{client_id}/delete", dict(name="Mein Client")
            ).status_code
            == 404
        )

    assert _client_values(app, db, foreign_id)[0] == "Mein Client"
    assert _client_values(app, db, own_user_client_id)[0] == "Mein Client"


# list and form


def test_list_excludes_apps_and_other_owners(client, seeder, utils, setup):
    user_id, admin_unit_id, client_id = setup
    seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    seeder.insert_default_oauth2_client(user_id=user_id)

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert body["items"] == [dict(id=client_id, client_name="Mein Client")]
    assert body["total"] == 1
    assert body["can_write"] is True


def test_list_validates_the_query(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    url = BASE_URL.format(admin_unit_id)

    assert utils.get_json(url + "?per_page=0").status_code == 422
    assert utils.get_json(url + "?page=2").status_code == 404


def test_form_lists_the_scopes(client, seeder, utils):
    from project.presentation.shared.scopes import scope_list

    _, admin_unit_id = seeder.setup_base()

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/form").json

    assert body["scopes"] == scope_list


# read


def test_read(client, app, db, seeder, utils):
    from sqlalchemy import text

    user_id, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    with app.app_context():
        db.session.execute(
            text("UPDATE oauth2_client SET created_by_id = :user_id WHERE id = :id"),
            {"id": client_id, "user_id": user_id},
        )
        db.session.commit()

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{client_id}").json

    assert body["client_name"] == "Mein Client"
    assert body["client_id"]
    assert body["client_secret"]
    assert body["scopes"] == body["scope"].split(" ")
    assert body["redirect_uris"]
    assert body["response_types"] == ["code"]
    assert body["audit"]["created_by_label"] == "test@test.de"
    assert body["can_write"] is True


# writes


def _save_body(**values):
    from project.presentation.shared.scopes import scope_list

    body = dict(
        client_name="Neuer Client",
        redirect_uris=["https://example.com/a", "  ", "https://example.com/b"],
        scopes=scope_list[:1],
    )
    body.update(values)
    return body


def test_create(client, app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.post_json(BASE_URL.format(admin_unit_id), _save_body())

    assert response.status_code == 201
    client_id = response.json["id"]
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/oauth2_client/{client_id}"
    )
    assert _flashes(client) == [("success", "OAuth2 Client erfolgreich erstellt")]
    name, scope, redirect_uris = _client_values(app, db, client_id)
    assert name == "Neuer Client"
    assert scope == _save_body()["scopes"][0]
    assert redirect_uris == ["https://example.com/a", "https://example.com/b"]


def test_create_validates(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    url = BASE_URL.format(admin_unit_id)

    response = utils.post_json(url, _save_body(client_name=""))
    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["client_name"]

    response = utils.post_json(url, _save_body(scopes=["unknown"]))
    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["scopes"]


def test_update(client, app, db, utils, setup):
    _, admin_unit_id, client_id = setup

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{client_id}",
        _save_body(client_name="Anderer Name"),
    )

    assert response.status_code == 200
    assert response.json["id"] == client_id
    assert _flashes(client) == [("success", "OAuth2 Client erfolgreich aktualisiert")]
    assert _client_values(app, db, client_id)[0] == "Anderer Name"


def test_update_validates_the_scopes(client, utils, setup):
    _, admin_unit_id, client_id = setup

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{client_id}", _save_body(scopes=["unknown"])
    )

    assert response.status_code == 422


def test_delete_needs_the_name(client, app, db, utils, setup):
    _, admin_unit_id, client_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{client_id}/delete",
        {"name": "Falscher Name"},
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert (
        response.json["errors"][0]["msg"]
        == "Der eingegebene Name entspricht nicht dem Namen des OAuth2 Clients"
    )
    assert _client_values(app, db, client_id) is not None


def test_delete_from_the_read_page_flashes_and_redirects(client, app, db, utils, setup):
    _, admin_unit_id, client_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{client_id}/delete",
        {"name": "mein client"},
    )

    assert response.status_code == 200
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/oauth2_clients"
    )
    assert _flashes(client) == [("success", "OAuth2 Client erfolgreich gelöscht")]
    assert _client_values(app, db, client_id) is None


def test_delete_from_the_list_does_not_flash(client, app, db, utils, setup):
    _, admin_unit_id, client_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{client_id}/delete",
        {"name": "Mein Client", "inline": True},
    )

    assert response.status_code == 200
    assert _flashes(client) == []
    assert _client_values(app, db, client_id) is None
