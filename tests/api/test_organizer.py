def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "organizerresource", organization_id=admin_unit_id, organizer_id=organizer_id
    )
    utils.get_ok(url)
