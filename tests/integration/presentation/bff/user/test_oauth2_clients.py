from project.presentation.shared.scopes import scopes
from tests.integration.presentation.bff.user.helpers import shell

LIST_URL = "/bff/user/oauth2-clients"
FORM_URL = "/bff/user/oauth2-clients/form"
ITEM_URL = "/bff/user/oauth2-clients/{}"
DELETE_URL = "/bff/user/oauth2-clients/{}/delete"


def _client(app, db, client_id):
    from project.infrastructure.models import OAuth2Client

    with app.app_context():
        found = db.session.get(OAuth2Client, client_id)
        return found and (found.client_name, found.scope, found.redirect_uris)


def _body(**values):
    body = dict(
        client_name="Neuer Client",
        redirect_uris=["/oauth2-redirect.html", "", "  https://example.com/cb "],
        scopes=["openid", "profile"],
    )
    body.update(values)
    return body


def _foreign_client(seeder):
    other_id = seeder.create_user(email="other@test.de")
    return seeder.insert_default_oauth2_client(other_id)


# access


def test_anonymous_is_401(client, seeder, utils):
    user_id = seeder.create_user()
    client_id = seeder.insert_default_oauth2_client(user_id)

    for call in (
        lambda: utils.get_json(LIST_URL),
        lambda: utils.get_json(FORM_URL),
        lambda: utils.get_json(ITEM_URL.format(client_id)),
        lambda: utils.post_json(LIST_URL, _body()),
        lambda: utils.put_json(ITEM_URL.format(client_id), _body()),
        lambda: utils.post_json(DELETE_URL.format(client_id), {"name": "x"}),
    ):
        assert call().status_code == 401


def test_writes_require_csrf(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)

    assert utils.post_json(LIST_URL, _body()).status_code == 400
    assert utils.put_json(ITEM_URL.format(client_id), _body()).status_code == 400
    assert (
        utils.post_json(DELETE_URL.format(client_id), {"name": "x"}).status_code == 400
    )


def test_a_foreign_client_is_403(client, app, db, seeder, utils):
    seeder.setup_base()
    shell(utils)
    foreign_id = _foreign_client(seeder)

    assert utils.get_json(ITEM_URL.format(foreign_id)).status_code == 403
    assert utils.put_json(ITEM_URL.format(foreign_id), _body()).status_code == 403
    assert (
        utils.post_json(
            DELETE_URL.format(foreign_id), {"name": "Mein Client"}
        ).status_code
        == 403
    )
    assert _client(app, db, foreign_id)[0] == "Mein Client"


def test_an_organization_client_is_403(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)

    assert utils.get_json(ITEM_URL.format(client_id)).status_code == 403


def test_an_unknown_client_is_404(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    assert utils.get_json(ITEM_URL.format(4711)).status_code == 404
    assert utils.put_json(ITEM_URL.format(4711), _body()).status_code == 404
    assert utils.post_json(DELETE_URL.format(4711), {"name": "x"}).status_code == 404


# list, form, read


def test_list(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)
    _foreign_client(seeder)

    body = utils.get_json_ok(LIST_URL).json

    assert [(i["id"], i["client_name"]) for i in body["items"]] == [
        (client_id, "Mein Client")
    ]
    assert utils.get_json(LIST_URL + "?page=2").status_code == 404


def test_form_offers_every_scope(client, seeder, utils):
    seeder.setup_base()

    assert utils.get_json_ok(FORM_URL).json == {"scopes": list(scopes)}


def test_read(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)

    body = utils.get_json_ok(ITEM_URL.format(client_id)).json

    assert body["client_name"] == "Mein Client"
    assert body["client_id"]
    assert body["client_secret"]
    assert body["scopes"] == body["scope"].split(" ")
    assert body["grant_types"]
    assert body["response_types"] == ["code"]
    assert body["token_endpoint_auth_method"]
    assert body["redirect_uris"]


# writes


def test_create(client, app, db, seeder, utils):
    seeder.setup_base()
    shell(utils)

    response = utils.post_json(LIST_URL, _body())

    assert response.status_code == 201
    assert _client(app, db, response.json["id"]) == (
        "Neuer Client",
        "openid profile",
        ["/oauth2-redirect.html", "https://example.com/cb"],
    )


def test_create_without_scopes_or_uris(client, app, db, seeder, utils):
    seeder.setup_base()
    shell(utils)

    response = utils.post_json(LIST_URL, {"client_name": "Leer"})

    assert response.status_code == 201
    assert _client(app, db, response.json["id"]) == ("Leer", "", [])


def test_create_validates_the_body(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    blank = utils.post_json(LIST_URL, _body(client_name=""))
    assert blank.status_code == 422
    assert blank.json["errors"][0]["loc"] == ["client_name"]

    unknown = utils.post_json(LIST_URL, _body(scopes=["openid", "nope"]))
    assert unknown.status_code == 422
    assert unknown.json["errors"][0]["loc"] == ["scopes"]


def test_update(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)
    shell(utils)

    response = utils.put_json(
        ITEM_URL.format(client_id), _body(client_name="Umbenannt", scopes=["openid"])
    )

    assert response.status_code == 204
    assert _client(app, db, client_id)[:2] == ("Umbenannt", "openid")


def test_update_validates_the_scopes(client, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)
    shell(utils)

    assert (
        utils.put_json(ITEM_URL.format(client_id), _body(scopes=["x"])).status_code
        == 422
    )


def test_delete_asks_for_the_name(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)
    shell(utils)

    wrong = utils.post_json(DELETE_URL.format(client_id), {"name": "Falsch"})
    assert wrong.status_code == 422
    assert wrong.json["errors"][0]["loc"] == ["name"]
    assert _client(app, db, client_id) is not None

    response = utils.post_json(DELETE_URL.format(client_id), {"name": "mein client"})

    assert response.status_code == 204
    assert _client(app, db, client_id) is None
