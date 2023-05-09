import pytest


@pytest.mark.parametrize("settings", [True, False])
def test_register(client, app, db, utils, settings):
    from project.services.user import find_user_by_email

    if settings:
        with app.app_context():
            from project.services.admin import upsert_settings

            settings = upsert_settings()
            settings.tos = "Meine Nutzungsbedingungen"
            db.session.commit()

    utils.register("test@test.de", "MeinPasswortIstDasBeste")

    with app.app_context():
        user = find_user_by_email("test@test.de")
        assert user is not None


def test_login(client, app, db, utils, seeder):
    seeder.create_user("test@test.de", "MeinPasswortIstDasBeste")
    user_id = utils.login("test@test.de", "MeinPasswortIstDasBeste")
    assert user_id is not None
