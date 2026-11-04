import pytest
from sqlalchemy import text

BASE_URL = "/bff/manage/organizations/{}/api-keys"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/api_keys")


def _api_key_name(app, db, api_key_id):
    from project.infrastructure.models import ApiKey

    with app.app_context():
        api_key = db.session.get(ApiKey, api_key_id)
        return api_key and api_key.name


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


def _insert_key(app, db, name, created_at, user_id=None, admin_unit_id=None):
    from project.infrastructure.models import ApiKey

    with app.app_context():
        api_key = ApiKey(name=name, user_id=user_id, admin_unit_id=admin_unit_id)
        api_key.generate_key()
        db.session.add(api_key)
        db.session.commit()
        db.session.execute(
            text("UPDATE apikey SET created_at = :created_at WHERE id = :id"),
            {"created_at": created_at, "id": api_key.id},
        )
        db.session.commit()
        return api_key.id


@pytest.fixture
def setup(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    api_key_id, key = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    _shell(utils, admin_unit_id)
    return user_id, admin_unit_id, api_key_id, key


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/1").status_code == 401
    assert utils.post_json(base, dict(name="x")).status_code == 401
    assert utils.put_json(f"{base}/1", dict(name="x")).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict(name="x")).status_code == 401


def test_member_without_permission_is_403(client, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/{api_key_id}").status_code == 403
    assert utils.post_json(base, dict(name="x")).status_code == 403
    assert utils.put_json(f"{base}/{api_key_id}", dict(name="x")).status_code == 403
    assert (
        utils.post_json(f"{base}/{api_key_id}/delete", dict(name="x")).status_code
        == 403
    )


def test_writes_require_csrf(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.post_json(base, dict(name="x")).status_code == 400
    assert utils.put_json(f"{base}/{api_key_id}", dict(name="x")).status_code == 400
    assert (
        utils.post_json(f"{base}/{api_key_id}/delete", dict(name="x")).status_code
        == 400
    )


def test_keys_of_others_are_404(client, app, db, seeder, utils, setup):
    user_id, admin_unit_id, _, _ = setup
    other_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id, _ = seeder.insert_default_api_key(admin_unit_id=other_unit_id)
    own_user_key_id, _ = seeder.insert_default_api_key(user_id=user_id)
    base = BASE_URL.format(admin_unit_id)

    for key_id in (foreign_id, own_user_key_id, 4711):
        assert utils.get_json(f"{base}/{key_id}").status_code == 404
        assert utils.put_json(f"{base}/{key_id}", dict(name="Neu")).status_code == 404
        assert (
            utils.post_json(
                f"{base}/{key_id}/delete", dict(name="Mein API Key")
            ).status_code
            == 404
        )

    assert _api_key_name(app, db, foreign_id) == "Mein API Key"
    assert _api_key_name(app, db, own_user_key_id) == "Mein API Key"


# list


def test_list_and_sort(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    _insert_key(app, db, "bravo", "2026-01-02", admin_unit_id=admin_unit_id)
    _insert_key(app, db, "Alpha", "2026-01-01", admin_unit_id=admin_unit_id)
    _insert_key(app, db, "charlie", "2026-01-03", admin_unit_id=admin_unit_id)
    _insert_key(app, db, "user key", "2026-01-04", user_id=user_id)
    _insert_key(app, db, "foreign", "2026-01-05", user_id=other_user_id)
    url = BASE_URL.format(admin_unit_id)

    def names(query=""):
        return [i["name"] for i in utils.get_json_ok(url + query).json["items"]]

    assert names() == ["Alpha", "bravo", "charlie"]
    assert names("?sort=name") == ["Alpha", "bravo", "charlie"]
    assert names("?sort=-created_at") == ["charlie", "bravo", "Alpha"]

    body = utils.get_json_ok(url).json
    assert body["total"] == 3
    assert body["can_write"] is True
    assert body["items"][0]["created_at"] is not None


def test_list_validates_the_query(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    url = BASE_URL.format(admin_unit_id)

    assert utils.get_json(url + "?per_page=0").status_code == 422
    assert utils.get_json(url + "?sort=unknown").status_code == 422
    assert utils.get_json(url + "?page=2").status_code == 404


# read


def test_read(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    api_key_id, key = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE apikey SET created_by_id = :user_id,"
                " created_at = '2026-01-02 10:00' WHERE id = :id"
            ),
            {"id": api_key_id, "user_id": user_id},
        )
        db.session.commit()

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{api_key_id}").json

    assert body["name"] == "Mein API Key"
    assert len(body["rate_limits"]) == 1
    assert body["rate_limits"][0].startswith("500 per 1 hour: ")
    assert body["audit"]["created_by_label"] == "test@test.de"
    assert body["can_write"] is True
    assert key not in str(body)


# writes


def test_create_returns_the_key_once(client, app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    response = utils.post_json(base, {"name": "Neuer Schluessel"})

    assert response.status_code == 201
    assert response.json["key"]
    assert _api_key_name(app, db, response.json["id"]) == "Neuer Schluessel"
    assert response.json["key"] not in str(utils.get_json_ok(base).json)
    assert response.json["key"] not in str(
        utils.get_json_ok(f"{base}/{response.json['id']}").json
    )


def test_create_is_limited(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.post_json(base, {"name": "Erster"}).status_code == 201
    response = utils.post_json(base, {"name": "Zweiter"})

    assert response.status_code == 400
    assert (
        response.json["message"]
        == "Die maximale Anzahl an API-Schlüsseln wurde erreicht."
    )


def test_create_needs_a_name(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    response = utils.post_json(BASE_URL.format(admin_unit_id), {"name": ""})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]


def test_update(client, app, db, utils, setup):
    _, admin_unit_id, api_key_id, _ = setup

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{api_key_id}", {"name": "Neuer Name"}
    )

    assert response.status_code == 200
    assert response.json["message"] == "API Schlüssel erfolgreich aktualisiert"
    assert _api_key_name(app, db, api_key_id) == "Neuer Name"


def test_delete_needs_the_name(client, app, db, utils, setup):
    _, admin_unit_id, api_key_id, _ = setup
    url = f"{BASE_URL.format(admin_unit_id)}/{api_key_id}/delete"

    response = utils.post_json(url, {"name": "Falscher Name"})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert (
        response.json["errors"][0]["msg"]
        == "Eingegebener Wert für Name stimmt nicht mit dem Wert in API Schlüssel  überein"
    )
    assert _api_key_name(app, db, api_key_id) == "Mein API Key"


def test_delete_from_the_read_page_flashes_and_redirects(client, app, db, utils, setup):
    _, admin_unit_id, api_key_id, _ = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{api_key_id}/delete",
        {"name": "mein api key"},
    )

    assert response.status_code == 200
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/api_keys"
    )
    assert response.json["message"] == "API Schlüssel erfolgreich gelöscht"
    assert _flashes(client) == [("success", "API Schlüssel erfolgreich gelöscht")]
    assert _api_key_name(app, db, api_key_id) is None


def test_delete_from_the_list_does_not_flash(client, app, db, utils, setup):
    _, admin_unit_id, api_key_id, _ = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{api_key_id}/delete",
        {"name": "Mein API Key", "inline": True},
    )

    assert response.status_code == 200
    assert _flashes(client) == []
    assert _api_key_name(app, db, api_key_id) is None
