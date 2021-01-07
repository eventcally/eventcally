def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("organizationresource", id=admin_unit_id)
    utils.get_ok(url)
