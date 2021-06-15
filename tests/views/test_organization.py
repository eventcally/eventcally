def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("organization", id=1)
    utils.get_ok(url)


def test_read_by_name(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("organization_by_name", au_short_name="meinecrew")
    utils.get_ok(url)
