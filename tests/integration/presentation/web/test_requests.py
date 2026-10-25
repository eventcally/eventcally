def test_api_responses_skip_the_site_headers(app, utils):
    app.config["API_READ_ANONYM"] = True

    response = utils.get_json_ok(utils.get_url("api_v1_organization_list"))

    assert "X-Frame-Options" not in response.headers
    assert "Content-Security-Policy" not in response.headers
