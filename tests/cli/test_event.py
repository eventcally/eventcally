def test_update_recurring_dates(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=7")

    runner = app.test_cli_runner()
    result = runner.invoke(args=["event", "update-recurring-dates"])
    assert result.exit_code == 0
