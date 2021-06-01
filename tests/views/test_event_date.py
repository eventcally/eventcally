def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())

    url = utils.get_url("event_date", id=1)
    utils.get_ok(url)

    url = utils.get_url("event_date", id=1, src="home")
    response = client.get(url)
    utils.assert_response_redirect(response, "event_date", id=1)


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())

    url = utils.get_url("event_date_ical", id=1)
    utils.get_ok(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("event_dates")
    utils.get_ok(url)

    url = utils.get_url("event_dates", keyword="name")
    utils.get_ok(url)

    url = utils.get_url("event_dates", category_id=2000)
    utils.get_ok(url)


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("event_date_search")
    utils.get_ok(url)
