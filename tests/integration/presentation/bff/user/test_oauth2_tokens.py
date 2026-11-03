import time

from tests.integration.presentation.bff.user.helpers import shell

LIST_URL = "/bff/user/oauth2-tokens"
ITEM_URL = "/bff/user/oauth2-tokens/{}"
REVOKE_URL = "/bff/user/oauth2-tokens/{}/revoke"


def _token_id(app, user_id):
    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        return OAuth2Token.query.filter(OAuth2Token.user_id == user_id).first().id


def _update_token(app, db, token_id, **values):
    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        token = db.session.get(OAuth2Token, token_id)

        for name, value in values.items():
            setattr(token, name, value)

        db.session.commit()


def _revoked(app, db, token_id):
    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        return bool(db.session.get(OAuth2Token, token_id).is_revoked())


def test_anonymous_is_401(client, utils):
    assert utils.get_json(LIST_URL).status_code == 401
    assert utils.get_json(ITEM_URL.format(1)).status_code == 401
    assert utils.post_json(REVOKE_URL.format(1), {}).status_code == 401


def test_list_and_status(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.login()
    token_id = _token_id(app, user_id)

    body = utils.get_json_ok(LIST_URL).json
    assert [i["id"] for i in body["items"]] == [token_id]
    item = body["items"][0]
    assert item["status"] is None
    assert item["client_name"]
    assert item["issued_at"] < item["expires_at"]

    now = int(time.time())
    _update_token(app, db, token_id, access_token_revoked_at=now)
    assert utils.get_json_ok(ITEM_URL.format(token_id)).json["status"] == "revoked"

    # An expired token is shown as expired even when it was revoked too.
    _update_token(app, db, token_id, issued_at=now - 100000, expires_in=60)
    assert utils.get_json_ok(ITEM_URL.format(token_id)).json["status"] == "expired"


def test_list_beyond_the_last_page_is_404(client, seeder, utils):
    seeder.setup_api_access()
    utils.login()

    assert utils.get_json(LIST_URL + "?page=2").status_code == 404


def test_a_foreign_token_is_403_and_an_unknown_one_404(client, app, seeder, utils):
    owner_id, admin_unit_id = seeder.setup_api_access()
    token_id = _token_id(app, owner_id)
    seeder.create_user("other@test.de")
    utils.login("other@test.de")
    shell(utils)

    assert utils.get_json(ITEM_URL.format(token_id)).status_code == 403
    assert utils.post_json(REVOKE_URL.format(token_id), {}).status_code == 403
    assert utils.get_json(ITEM_URL.format(4711)).status_code == 404
    assert utils.post_json(REVOKE_URL.format(4711), {}).status_code == 404


def test_revoke(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_api_access()
    utils.login()
    token_id = _token_id(app, user_id)
    shell(utils)

    response = utils.post_json(REVOKE_URL.format(token_id), {})

    assert response.status_code == 204
    assert _revoked(app, db, token_id)

    # A token cannot be revoked twice.
    assert utils.post_json(REVOKE_URL.format(token_id), {}).status_code == 400
