def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("planing")
    utils.get_ok(url)

    url = utils.get_url("planing", keyword="name")
    utils.get_ok(url)
