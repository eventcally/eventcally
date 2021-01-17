def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_date", id=1)
    utils.get_ok(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_date_list")
    utils.get_ok(url)


def test_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_event_date_search")
    utils.get_ok(url)
