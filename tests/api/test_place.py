def test_read(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    utils.get_ok(url)
