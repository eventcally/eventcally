def test_clear_admin_unit_dumps(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        from project.services.dump import clear_admin_unit_dumps

        clear_admin_unit_dumps()


def test_dump_admin_unit(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    image_id = seeder.upsert_default_image()
    seeder.assign_image_to_event(event_id, image_id)

    with app.app_context():
        from project.services.dump import dump_admin_unit

        dump_admin_unit(admin_unit_id)
