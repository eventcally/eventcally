def test_update_recurring_dates(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=7")

    runner = app.test_cli_runner()
    result = runner.invoke(args=["event", "update-recurring-dates"])
    assert result.exit_code == 0


def _create_event(seeder, admin_unit_id, postalCode):
    from project.models import Location

    return seeder.create_event(
        admin_unit_id,
        place_id=seeder.upsert_event_place(
            admin_unit_id,
            postalCode,
            Location(
                postalCode=postalCode,
            ),
        ),
    )


def test_create_bulk_event_references(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id_own = _create_event(seeder, admin_unit_id, "38640")

    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew", verified=True)
    event_id_38640 = _create_event(seeder, other_admin_unit_id, "38640")
    event_id_38690 = _create_event(seeder, other_admin_unit_id, "38690")
    event_id_55555 = _create_event(seeder, other_admin_unit_id, "55555")

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=[
            "event",
            "create-bulk-references",
            str(admin_unit_id),
            "38640",
            "38642",
            "38644",
            "38690",
        ]
    )
    assert result.exit_code == 0

    with app.app_context():
        from project.models import EventReference

        assert (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id_38640)
            .first()
        )
        assert (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id_38690)
            .first()
        )
        assert (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id_55555)
            .first()
        ) is None
        assert (
            EventReference.query.filter(EventReference.admin_unit_id == admin_unit_id)
            .filter(EventReference.event_id == event_id_own)
            .first()
        ) is None
