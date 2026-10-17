"""Parity of the user's OAuth2 token pages. Written against the ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _token_id(app, user_id):
    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        return OAuth2Token.query.filter(OAuth2Token.user_id == user_id).first().id


def test_token_pages(app, seeder, utils):
    user_id, _ = seeder.setup_api_access()
    utils.login()
    token_id = _token_id(app, user_id)

    response = utils.get_ok(utils.get_url("user.oauth2_tokens"))
    rows = utils.get_soup(response).select("table tbody tr")
    assert len(rows) == 1
    row = " ".join(rows[0].get_text().split())
    assert row.startswith(f"{token_id} Widerrufen Mein Client openid profile")
    assert row.endswith(" None")

    response = utils.get_ok(
        utils.get_url("user.oauth2_token_revoke", oauth2_token_id=token_id)
    )
    text = _text(utils, response)
    assert f"'OAuth2 Token {token_id} (Mein Client)'" in text


def test_foreign_and_unknown_tokens(app, seeder, utils):
    other_user_id, _ = seeder.setup_api_access()
    token_id = _token_id(app, other_user_id)
    seeder.create_user("second@test.de")
    utils.login("second@test.de")

    utils.get_unauthorized(
        utils.get_url("user.oauth2_token_revoke", oauth2_token_id=token_id)
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("user.oauth2_token_revoke", oauth2_token_id=4711))
    )
