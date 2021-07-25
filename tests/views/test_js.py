def test_js_check_org_short_name(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_short_name")
        response = utils.post_form_data(
            url,
            {
                "short_name": "meinecrew",
            },
        )
        utils.assert_response_ok(response)
        assert response.data == b"true"


def test_js_check_org_short_name_exists(client, seeder, utils):
    seeder.create_user(admin=True)
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_short_name")
        response = utils.post_form_data(
            url,
            {
                "short_name": "meinecrew",
            },
        )
        utils.assert_response_ok(response)
        assert response.data == b'"Der Kurzname ist bereits vergeben"'
