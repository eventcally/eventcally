def test_clear_images(client, seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()
    image_id = seeder.upsert_default_image()

    url = utils.get_image_url_for_id(image_id)
    utils.get_ok(url)

    runner = app.test_cli_runner()
    result = runner.invoke(args=["cache", "clear-images"])
    assert "Done." in result.output
