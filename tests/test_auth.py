from project.services.user import find_user_by_email, upsert_user


def test_register(client, app, utils):
    utils.register("test@test.de", "MeinPasswortIstDasBeste")

    with app.app_context():
        user = find_user_by_email("test@test.de")
        assert user is not None


def test_login(client, app, db, utils):
    with app.app_context():
        upsert_user("test@test.de", "MeinPasswortIstDasBeste")
        db.session.commit()

    utils.login("test@test.de", "MeinPasswortIstDasBeste")
