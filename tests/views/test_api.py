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


def test_infoscreen(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)
    au_short_name = "meinecrew"

    url = utils.get_url("api_infoscreen", au_short_name=au_short_name)
    utils.get_ok(url)


def test_event_places(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    url = utils.get_url("api_event_places", id=organizer_id)
    utils.get_ok(url)
