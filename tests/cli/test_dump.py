def test_all(client, seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=7")

    runner = app.test_cli_runner()
    result = runner.invoke(args=["dump", "all"])
    assert "Zipped all up" in result.output

    utils.get_endpoint_ok("developer")
    utils.get_endpoint_ok("dump_files", path="all.zip")
