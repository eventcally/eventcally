def test_normal_user(client, seeder, utils):
    seeder.create_user()
    utils.login()
    response = client.get("/admin")
    assert response.status_code == 403


def test_admin_user(client, seeder, utils, app):
    seeder.create_user(admin=True)
    utils.login()
    response = client.get("/admin")
    assert response.status_code == 200


def test_admin_units(client, seeder, utils, app):
    seeder.create_user(admin=True)
    user = utils.login()
    seeder.create_admin_unit(user, "Meine Crew")
    response = client.get("/admin/admin_units")
    assert b"Meine Crew" in response.data
