def test_authorize_unauthorizedRedirects(seeder, utils):
    url = utils.get_url("authorize")
    response = utils.get(url)

    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_authorize_validateThrowsError(seeder, utils):
    seeder.setup_base()
    url = utils.get_url("authorize")
    response = utils.get(url)

    utils.assert_response_bad_request(response)


def test_revoke_token(seeder, utils):
    seeder.setup_api_access()
    utils.revoke_token()


def test_introspect(seeder, utils):
    seeder.setup_api_access()
    utils.introspect(utils.get_access_token(), "access_token")
    utils.introspect(utils.get_refresh_token(), "refresh_token")
    utils.introspect(utils.get_access_token(), "")
    utils.introspect(utils.get_refresh_token(), "")


def test_swagger_redirect(utils):
    url = utils.get_url("swagger_oauth2_redirect")
    response = utils.get(url)
    assert response.status_code == 302


def test_oauth_userinfo(seeder, utils):
    seeder.setup_api_access()
    utils.get_oauth_userinfo()


def test_jwks(utils):
    utils.get_endpoint_ok("jwks")


def test_openid_configuration(utils):
    utils.get_endpoint_ok("openid_configuration")
