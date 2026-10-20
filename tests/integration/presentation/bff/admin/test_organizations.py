def _login_admin(seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    utils.get_ok(
        "/admin-next/organizations"
    )  # picks up the CSRF token of the Vue 3 shell


def _create_org(seeder, name="Alpha", **kwargs):
    owner_id = seeder.create_user(email=f"{name.lower()}@test.de")
    return seeder.create_admin_unit(owner_id, name=name, **kwargs)


def _login_non_admin(seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok("/")  # a non-admin cannot load the shell; the legacy layout has one


def test_organizations(client, seeder, utils):
    _login_admin(seeder, utils)
    _create_org(seeder, "Beta")
    _create_org(seeder, "alpha")

    body = utils.get_json_ok("/bff/admin/organizations").json

    assert [o["name"] for o in body["items"]] == ["alpha", "Beta"]
    row = body["items"][0]
    assert {"id", "is_verified", "created_at", "deletion_requested_at"} <= set(row)
    assert body["total"] == 2
    assert body["pages"] == 1
    assert body["page"] == 1


def test_organizations_keyword(client, seeder, utils):
    _login_admin(seeder, utils)
    _create_org(seeder, "Beta")
    _create_org(seeder, "alpha")

    body = utils.get_json_ok("/bff/admin/organizations?keyword=alp").json
    assert [o["name"] for o in body["items"]] == ["alpha"]

    body = utils.get_json_ok("/bff/admin/organizations?keyword=%20%20").json
    assert body["total"] == 2


def test_organizations_page_out_of_range(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.get_json("/bff/admin/organizations?page=2")

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"


def test_organizations_invalid_page(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.get_json("/bff/admin/organizations?page=0")

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["page"]


def test_organizations_forbidden(client, seeder, utils):
    seeder.create_user()
    utils.login()

    response = utils.get_json("/bff/admin/organizations")

    utils.assert_response_forbidden(response)


def test_organizations_unauthorized(client, utils):
    utils.assert_response_unauthorized(utils.get_json("/bff/admin/organizations"))


def test_organization(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder, "Alpha", can_create_other=True)

    body = utils.get_json_ok(f"/bff/admin/organizations/{org_id}").json

    assert body["id"] == org_id
    assert body["name"] == "Alpha"
    assert body["can_create_other"] is True
    assert body["can_invite_other"] is True
    assert body["can_verify_other"] is False
    assert "incoming_reference_requests_allowed" in body
    assert body["audit"]["created_at"]


def test_organization_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    utils.assert_response_notFound(utils.get_json("/bff/admin/organizations/12345"))


def test_organization_forbidden(client, seeder, utils):
    org_id = _create_org(seeder)
    _login_non_admin(seeder, utils)

    response = utils.get_json(f"/bff/admin/organizations/{org_id}")

    utils.assert_response_forbidden(response)


def test_organization_forbidden_missing_id_is_404(client, seeder, utils):
    # The query handler returns None before it checks the actor.
    _login_non_admin(seeder, utils)

    utils.assert_response_notFound(utils.get_json("/bff/admin/organizations/12345"))


def test_organization_unauthorized(client, utils):
    utils.assert_response_unauthorized(utils.get_json("/bff/admin/organizations/1"))


def test_update_organization_setting(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder, can_create_other=True, can_invite_other=False)
    url = f"/bff/admin/organizations/{org_id}/settings/can_invite_other"

    response = utils.put_json(url, {"value": True})

    utils.assert_response_ok(response)
    body = response.json
    assert body["can_invite_other"] is True
    assert body["can_create_other"] is True  # untouched
    assert body["can_verify_other"] is False
    assert body["audit"]["updated_at"]

    body = utils.put_json(url, {"value": False}).json
    assert body["can_invite_other"] is False
    assert body["can_create_other"] is True


def test_update_organization_setting_unknown_key(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder)

    response = utils.put_json(
        f"/bff/admin/organizations/{org_id}/settings/name", {"value": True}
    )

    utils.assert_response_notFound(response)


def test_update_organization_setting_missing_value(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder)

    response = utils.put_json(
        f"/bff/admin/organizations/{org_id}/settings/can_invite_other", {}
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["value"]


def test_update_organization_setting_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.put_json(
        "/bff/admin/organizations/12345/settings/can_invite_other", {"value": True}
    )

    utils.assert_response_notFound(response)


def test_update_organization_setting_forbidden(client, seeder, utils):
    org_id = _create_org(seeder)
    _login_non_admin(seeder, utils)

    response = utils.put_json(
        f"/bff/admin/organizations/{org_id}/settings/can_invite_other", {"value": True}
    )

    utils.assert_response_forbidden(response)


def test_update_organization_setting_unauthorized(client, utils):
    response = utils.put_json(
        "/bff/admin/organizations/1/settings/can_invite_other", {"value": True}
    )

    utils.assert_response_unauthorized(response)


def test_update_organization_setting_without_csrf(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    org_id = _create_org(seeder)

    response = utils.put_json(
        f"/bff/admin/organizations/{org_id}/settings/can_invite_other", {"value": True}
    )

    utils.assert_response_bad_request(response)


def test_delete_organization(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder, "Alpha")

    response = utils.delete(f"/bff/admin/organizations/{org_id}", {"name": "ALPHA "})

    utils.assert_response_no_content(response)
    utils.assert_response_notFound(utils.get_json(f"/bff/admin/organizations/{org_id}"))


def test_delete_organization_name_mismatch(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder, "Alpha")

    response = utils.delete(f"/bff/admin/organizations/{org_id}", {"name": "Beta"})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["name"]
    utils.get_json_ok(f"/bff/admin/organizations/{org_id}")


def test_delete_organization_missing_body(client, seeder, utils):
    _login_admin(seeder, utils)
    org_id = _create_org(seeder)

    response = utils.delete(f"/bff/admin/organizations/{org_id}")

    utils.assert_response_unprocessable_entity(response)


def test_delete_organization_not_found(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.delete("/bff/admin/organizations/12345", {"name": "Alpha"})

    utils.assert_response_notFound(response)


def test_delete_organization_forbidden(client, seeder, utils):
    org_id = _create_org(seeder)
    _login_non_admin(seeder, utils)

    response = utils.delete(f"/bff/admin/organizations/{org_id}", {"name": "Alpha"})

    utils.assert_response_forbidden(response)


def test_delete_organization_unauthorized(client, utils):
    response = utils.delete("/bff/admin/organizations/1", {"name": "Alpha"})

    utils.assert_response_unauthorized(response)


def test_delete_organization_without_csrf(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    org_id = _create_org(seeder)

    response = utils.delete(f"/bff/admin/organizations/{org_id}", {"name": "Alpha"})

    utils.assert_response_bad_request(response)
