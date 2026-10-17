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


def test_dump_collects_every_keyset_batch(client, seeder, app, monkeypatch):
    user_id, admin_unit_id = seeder.setup_base()
    for index in range(3):
        seeder.create_event(admin_unit_id, name=f"Event {index}")

    with app.app_context():
        from project.services import dump

        monkeypatch.setattr(dump, "BATCH_SIZE", 2)
        events = dump._collect(
            lambda after_id: dump.ListDumpEventsQuery(
                admin_unit_id=admin_unit_id, after_id=after_id, limit=2
            )
        )

        assert [event.name for event in events] == ["Event 0", "Event 1", "Event 2"]
