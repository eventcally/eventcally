import pytest


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.login()

    url = utils.get_url("oauth2_tokens")
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
def test_revoke(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_api_access()
    utils.login()

    with app.app_context():
        from project.models import OAuth2Token

        oauth2_token = OAuth2Token.query.filter(OAuth2Token.user_id == user_id).first()
        oauth2_token_id = oauth2_token.id

    url = utils.get_url("oauth2_token_revoke", id=oauth2_token_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "oauth2_tokens")

    with app.app_context():
        from project.models import OAuth2Token

        oauth2_token = db.session.get(OAuth2Token, oauth2_token_id)
        assert oauth2_token.is_revoked() > 0

    # Kann nicht zweimal revoked werden
    response = utils.get(url)
    utils.assert_response_redirect(response, "oauth2_tokens")
