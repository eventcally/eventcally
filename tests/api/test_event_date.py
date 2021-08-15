def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)
    url = utils.get_url("api_v1_event_date", id=1)
    utils.get_ok(url)

    seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("api_v1_event_date", id=2)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_date_list")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == 1


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("api_v1_event_date_search", sort="-rating")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert response.json["items"][0]["start"].endswith("+02:00")
