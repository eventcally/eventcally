def test_events(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_events")
    utils.get_ok(url)


def test_event_dates(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_event_dates")
    utils.get_ok(url)

    url = utils.get_url("api_event_dates", keyword="name")
    utils.get_ok(url)

    url = utils.get_url("api_event_dates", category_id=2000)
    utils.get_ok(url)

    url = utils.get_url("api_event_dates", category_id=0)
    utils.get_ok(url)

    url = utils.get_url("api_event_dates", weekday=1)
    utils.get_ok(url)

    url = utils.get_url(
        "api_event_dates", coordinate="51.9077888,10.4333312", distance=500
    )
    utils.get_ok(url)

    url = utils.get_url("api_event_dates", date_from="2020-10-03", date_to="2021-10-03")
    utils.get_ok(url)

    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    url = utils.get_url("api_event_dates", organizer_id=organizer_id)
    utils.get_ok(url)
