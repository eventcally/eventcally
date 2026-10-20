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


def _login_admin(seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    utils.get_ok("/admin-next/users")  # picks up the CSRF token of the Vue 3 shell


def _other_user_id(seeder, email="other@test.de"):
    return seeder.create_user(email=email)


def test_user(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    body = utils.get_json_ok(f"/bff/admin/users/{other_id}").json

    assert body["user"]["id"] == other_id
    assert body["user"]["email"] == "other@test.de"
    assert body["user"]["roles"] == []
    admin = next(r for r in body["available_roles"] if r["name"] == "admin")
    assert admin["title"]


def test_user_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.get_json("/bff/admin/users/12345")

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"


def test_user_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()

    response = utils.get_json("/bff/admin/users/1")

    utils.assert_response_forbidden(response)
    assert response.json["name"] == "Forbidden"


def test_user_unauthorized(client, utils):
    utils.assert_response_unauthorized(utils.get_json("/bff/admin/users/1"))


def test_update_user_roles(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.put_json(
        f"/bff/admin/users/{other_id}/roles", {"roles": ["admin", "admin"]}
    )

    utils.assert_response_no_content(response)
    body = utils.get_json_ok(f"/bff/admin/users/{other_id}").json
    assert body["user"]["roles"] == ["admin"]

    response = utils.put_json(f"/bff/admin/users/{other_id}/roles", {"roles": []})

    utils.assert_response_no_content(response)
    assert utils.get_json_ok(f"/bff/admin/users/{other_id}").json["user"]["roles"] == []


def test_update_user_roles_unknown_role(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.put_json(f"/bff/admin/users/{other_id}/roles", {"roles": ["nope"]})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["roles"]


def test_update_user_roles_invalid_body(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.put_json(f"/bff/admin/users/{other_id}/roles", {})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["roles"]


def test_update_user_roles_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.put_json("/bff/admin/users/12345/roles", {"roles": []})

    utils.assert_response_notFound(response)


def test_update_user_roles_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok(
        "/"
    )  # a non-admin cannot load the shell; the legacy layout has a token

    response = utils.put_json("/bff/admin/users/1/roles", {"roles": []})

    utils.assert_response_forbidden(response)


def test_update_user_roles_without_csrf(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    other_id = _other_user_id(seeder)

    response = utils.put_json(f"/bff/admin/users/{other_id}/roles", {"roles": []})

    utils.assert_response_bad_request(response)


def test_delete_user(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.delete(f"/bff/admin/users/{other_id}", {"email": "other@test.de"})

    utils.assert_response_no_content(response)
    utils.assert_response_notFound(utils.get_json(f"/bff/admin/users/{other_id}"))


def test_delete_user_email_case_insensitive(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.delete(f"/bff/admin/users/{other_id}", {"email": "OTHER@Test.de"})

    utils.assert_response_no_content(response)


def test_delete_user_email_mismatch(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.delete(f"/bff/admin/users/{other_id}", {"email": "wrong@test.de"})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["email"]
    utils.get_json_ok(f"/bff/admin/users/{other_id}")


def test_delete_user_missing_body(client, seeder, utils):
    _login_admin(seeder, utils)
    other_id = _other_user_id(seeder)

    response = utils.delete(f"/bff/admin/users/{other_id}")

    utils.assert_response_unprocessable_entity(response)


def test_delete_user_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.delete("/bff/admin/users/12345", {"email": "other@test.de"})

    utils.assert_response_notFound(response)


def test_delete_user_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok(
        "/"
    )  # a non-admin cannot load the shell; the legacy layout has a token

    response = utils.delete("/bff/admin/users/1", {"email": "a@b.de"})

    utils.assert_response_forbidden(response)
