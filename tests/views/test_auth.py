from project.services.user import find_user_by_email


def test_register(client, app, utils):
    utils.register("test@test.de", "MeinPasswortIstDasBeste")

    with app.app_context():
        user = find_user_by_email("test@test.de")
        assert user is not None


def test_login(client, app, db, utils, seeder):
    seeder.create_user("test@test.de", "MeinPasswortIstDasBeste")
    user_id = utils.login("test@test.de", "MeinPasswortIstDasBeste")
    assert user_id is not None
