def test_seed(client, seeder, app, utils, caplog):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["data", "seed"])
    assert result.exit_code == 0
