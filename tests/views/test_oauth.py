def test_authorize_unauthorizedRedirects(seeder, utils):
    url = utils.get_url("authorize")
    response = utils.get(url)

    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_authorize_validateThrowsError(seeder, utils):
    seeder.setup_base()
    url = utils.get_url("authorize")
    response = utils.get(url)

    utils.assert_response_error_message(response, b"invalid_grant")


def test_revoke_token(seeder, utils):
    seeder.setup_api_access()
    utils.revoke_token()


def test_swagger_redirect(utils):
    url = utils.get_url("swagger_oauth2_redirect")
    response = utils.get(url)
    assert response.status_code == 302
