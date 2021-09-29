def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)
    url = utils.get_url("api_v1_event_date", id=1)
    utils.get_ok(url)

    seeder.create_event(admin_unit_id, draft=True)
    draft_url = utils.get_url("api_v1_event_date", id=2)
    response = utils.get(draft_url)
    utils.assert_response_unauthorized(response)

    seeder.create_event_unverified()
    unverified_url = utils.get_url("api_v1_event_date", id=3)
    response = utils.get(unverified_url)
    utils.assert_response_unauthorized(response)

    seeder.authorize_api_access(user_id, admin_unit_id)
    response = utils.get_json(draft_url)
    utils.assert_response_ok(response)


def test_read_myUnverified(client, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access(admin_unit_verified=False)
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_date", id=1)
    response = utils.get_json(url)
    utils.assert_response_ok(response)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_event_date_list")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == 1


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    seeder.create_event_unverified()

    url = utils.get_url("api_v1_event_date_search", sort="-rating")
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
    assert response.json["items"][0]["start"].endswith("+02:00")

    url = utils.get_url("api_v1_event_date_search", keyword="name")
    response = utils.get_ok(url)

    url = utils.get_url("api_v1_event_date_search", category_id=0)
    response = utils.get_ok(url)

    url = utils.get_url("api_v1_event_date_search", category_id=2000)
    response = utils.get_ok(url)

    url = utils.get_url("api_v1_event_date_search", weekday=1)
    response = utils.get_ok(url)

    url = utils.get_url(
        "api_v1_event_date_search", date_from="2020-10-03", date_to="2021-10-03"
    )
    response = utils.get_ok(url)

    url = utils.get_url(
        "api_v1_event_date_search", coordinate="51.9077888,10.4333312", distance=500
    )
    response = utils.get_ok(url)

    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    url = utils.get_url("api_v1_event_date_search", organizer_id=organizer_id)
    response = utils.get_ok(url)


def test_search_oneDay(client, seeder, utils):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base()

    start = create_berlin_date(2020, 10, 3, 10)
    end = create_berlin_date(2020, 10, 3, 11)
    name = "Spezialveranstaltung"
    event_id = seeder.create_event(admin_unit_id, name=name, start=start, end=end)

    url = utils.get_url(
        "api_v1_event_date_search", date_from="2020-10-03", date_to="2020-10-03"
    )
    response = utils.get_ok(url)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["event"]["id"] == event_id
