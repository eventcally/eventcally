def test_js_js_check_register_email(client, seeder, utils):
    url = utils.get_url("security.register")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_register_email")
        response = utils.post_form_data(
            url,
            {
                "email": "test@test.de",
            },
        )
        utils.assert_response_ok(response)
        assert response.data == b"true"


def test_js_js_check_register_email_exists(client, seeder, utils):
    seeder.create_user()
    url = utils.get_url("security.register")
    response = utils.get(url)

    url = utils.get_url("js_check_register_email")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_register_email")
        response = utils.post_form_data(
            url,
            {
                "email": "test@test.de",
            },
        )
        utils.assert_response_ok(response)
        assert response.data == b'"Mit dieser E-Mail existiert bereits ein Account."'
