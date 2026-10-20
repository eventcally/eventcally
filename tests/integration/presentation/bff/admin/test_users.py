def test_users(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = utils.get_json_ok("/bff/admin/users")

    body = response.json
    assert body["items"][0]["email"] == "test@test.de"
    assert "admin" in body["items"][0]["roles"]
    assert body["total"] == 1
    assert body["pages"] == 1
    assert body["page"] == 1


def test_users_invalid_page(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = utils.get_json("/bff/admin/users?page=0")

    utils.assert_response_unprocessable_entity(response)
    assert response.json["name"] == "Unprocessable Entity"
    assert response.json["errors"][0]["loc"] == ["page"]


def test_users_page_out_of_range(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    response = utils.get_json("/bff/admin/users?page=2")

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"


def test_users_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()

    response = utils.get_json("/bff/admin/users")

    utils.assert_response_forbidden(response)
    assert response.json["name"] == "Forbidden"


def test_users_unauthorized(client, utils):
    response = utils.get_json("/bff/admin/users")

    utils.assert_response_unauthorized(response)
