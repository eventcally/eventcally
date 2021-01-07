def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("eventresource", id=event_id)
    utils.get_ok(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("eventlistresource")
    utils.get_ok(url)
