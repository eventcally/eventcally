def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    image_id = seeder.upsert_default_image()

    url = utils.get_url("imageresource", id=image_id)
    utils.get_ok(url)
