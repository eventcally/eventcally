from tests.integration.presentation.bff.user.helpers import shell

LIST_URL = "/bff/user/api-keys"
ITEM_URL = "/bff/user/api-keys/{}"
DELETE_URL = "/bff/user/api-keys/{}/delete"


def _api_key(app, db, api_key_id):
    from project.infrastructure.models import ApiKey

    with app.app_context():
        api_key = db.session.get(ApiKey, api_key_id)
        return api_key and api_key.name


def _foreign_key(seeder, utils, admin_unit_id=None):
    other_id = seeder.create_user(email="other@test.de")
    return seeder.insert_default_api_key(other_id)[0]


# access


def test_anonymous_is_401(client, seeder, utils):
    user_id = seeder.create_user()
    api_key_id, _ = seeder.insert_default_api_key(user_id)

    for call in (
        lambda: utils.get_json(LIST_URL),
        lambda: utils.get_json(ITEM_URL.format(api_key_id)),
        lambda: utils.post_json(LIST_URL, {"name": "x"}),
        lambda: utils.put_json(ITEM_URL.format(api_key_id), {"name": "x"}),
        lambda: utils.post_json(DELETE_URL.format(api_key_id), {"name": "x"}),
    ):
        assert call().status_code == 401


def test_writes_require_csrf(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(user_id)

    assert utils.post_json(LIST_URL, {"name": "x"}).status_code == 400
    assert utils.put_json(ITEM_URL.format(api_key_id), {"name": "x"}).status_code == 400
    assert (
        utils.post_json(DELETE_URL.format(api_key_id), {"name": "x"}).status_code == 400
    )


def test_a_foreign_key_is_403(client, app, db, seeder, utils):
    seeder.setup_base()
    shell(utils)
    foreign_id = _foreign_key(seeder, utils)

    assert utils.get_json(ITEM_URL.format(foreign_id)).status_code == 403
    assert utils.put_json(ITEM_URL.format(foreign_id), {"name": "x"}).status_code == 403
    assert (
        utils.post_json(
            DELETE_URL.format(foreign_id), {"name": "Mein API Key"}
        ).status_code
        == 403
    )
    assert _api_key(app, db, foreign_id) == "Mein API Key"


def test_an_organization_key_is_403(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    assert utils.get_json(ITEM_URL.format(api_key_id)).status_code == 403


def test_an_unknown_key_is_404(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    assert utils.get_json(ITEM_URL.format(4711)).status_code == 404
    assert utils.put_json(ITEM_URL.format(4711), {"name": "x"}).status_code == 404
    assert utils.post_json(DELETE_URL.format(4711), {"name": "x"}).status_code == 404


# list


def test_list_and_sort(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    seeder.insert_default_api_key(user_id)
    _foreign_key(seeder, utils)

    body = utils.get_json_ok(LIST_URL).json

    assert [i["name"] for i in body["items"]] == ["Mein API Key"]
    assert body["total"] == 1
    assert body["items"][0]["created_at"] is not None

    assert utils.get_json_ok(LIST_URL + "?sort=name").json["total"] == 1
    assert utils.get_json_ok(LIST_URL + "?sort=-created_at").json["total"] == 1


def test_list_sorts_by_name_or_by_creation(client, app, db, seeder, utils):
    from sqlalchemy import text

    from project.infrastructure.models import ApiKey

    user_id, _ = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")

    with app.app_context():
        for name, created_at, owner_id in (
            ("bravo", "2026-01-02", user_id),
            ("Alpha", "2026-01-01", user_id),
            ("charlie", "2026-01-03", user_id),
            ("foreign", "2026-01-04", other_user_id),
        ):
            api_key = ApiKey(name=name, user_id=owner_id)
            api_key.generate_key()
            db.session.add(api_key)
            db.session.commit()
            db.session.execute(
                text("UPDATE apikey SET created_at = :created_at WHERE id = :id"),
                {"created_at": created_at, "id": api_key.id},
            )
            db.session.commit()

    def names(url):
        return [i["name"] for i in utils.get_json_ok(url).json["items"]]

    assert names(LIST_URL) == ["Alpha", "bravo", "charlie"]
    assert names(LIST_URL + "?sort=-created_at") == ["charlie", "bravo", "Alpha"]


def test_list_validates_the_query(client, seeder, utils):
    seeder.setup_base()

    assert utils.get_json(LIST_URL + "?per_page=0").status_code == 422
    assert utils.get_json(LIST_URL + "?sort=unknown").status_code == 422
    assert utils.get_json(LIST_URL + "?page=2").status_code == 404


# read


def test_read(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    api_key_id, key = seeder.insert_default_api_key(user_id)

    body = utils.get_json_ok(ITEM_URL.format(api_key_id)).json

    assert body["name"] == "Mein API Key"
    assert body["created_at"] is not None
    assert body["rate_limits"]
    assert all("remaining" in row for row in body["rate_limits"])
    assert key not in str(body)


# writes


def test_create_returns_the_key_once(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    shell(utils)

    response = utils.post_json(LIST_URL, {"name": "Neuer Schluessel"})

    assert response.status_code == 201
    assert response.json["key"]
    assert _api_key(app, db, response.json["id"]) == "Neuer Schluessel"
    assert response.json["key"] not in str(utils.get_json_ok(LIST_URL).json)
    assert response.json["key"] not in str(
        utils.get_json_ok(ITEM_URL.format(response.json["id"])).json
    )


def test_create_is_limited(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    seeder.insert_default_api_key(user_id)
    shell(utils)

    response = utils.post_json(LIST_URL, {"name": "Zweiter"})

    assert response.status_code == 400
    assert (
        response.json["message"]
        == "Die maximale Anzahl an API-Schlüsseln wurde erreicht."
    )


def test_create_needs_a_name(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    response = utils.post_json(LIST_URL, {"name": ""})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]


def test_update(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(user_id)
    shell(utils)

    response = utils.put_json(ITEM_URL.format(api_key_id), {"name": "Neuer Name"})

    assert response.status_code == 204
    assert _api_key(app, db, api_key_id) == "Neuer Name"


def test_delete_asks_for_the_name(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(user_id)
    shell(utils)

    wrong = utils.post_json(DELETE_URL.format(api_key_id), {"name": "Falscher Name"})
    assert wrong.status_code == 422
    assert wrong.json["errors"][0]["loc"] == ["name"]
    assert _api_key(app, db, api_key_id) == "Mein API Key"

    response = utils.post_json(DELETE_URL.format(api_key_id), {"name": "mein api key"})

    assert response.status_code == 204
    assert _api_key(app, db, api_key_id) is None
