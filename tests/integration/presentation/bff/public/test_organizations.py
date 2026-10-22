LIST_URL = "/bff/public/organizations"


def _url(organization_id):
    return f"{LIST_URL}/{organization_id}"


def _create_org(seeder, name, email=None, **kwargs):
    owner_id = seeder.create_user(email=email or f"{name.lower()}@test.de")
    return owner_id, seeder.create_admin_unit(owner_id, name=name, **kwargs)


def _names(body):
    return [o["name"] for o in body["items"]]


# list


def test_list_anonymous_only_verified(client, seeder, utils):
    _create_org(seeder, "Verified", verified=True)
    _create_org(seeder, "Hidden")

    body = utils.get_json_ok(LIST_URL).json

    assert "Verified" in _names(body)
    assert "Hidden" not in _names(body)
    row = next(o for o in body["items"] if o["name"] == "Verified")
    assert row["short_name"] == "verified"
    assert row["is_verified"] is True
    assert body["page"] == 1
    assert body["per_page"] == 20


def test_list_keyword(client, seeder, utils):
    _create_org(seeder, "Alpha", verified=True)
    _create_org(seeder, "Beta", verified=True)

    assert _names(utils.get_json_ok(f"{LIST_URL}?keyword=alp").json) == ["Alpha"]
    assert _names(utils.get_json_ok(f"{LIST_URL}?keyword=%20%20").json) != ["Alpha"]


def test_list_paging(client, seeder, utils):
    for i in range(3):
        _create_org(seeder, f"Org{i}", verified=True)

    body = utils.get_json_ok(f"{LIST_URL}?per_page=2&keyword=org").json
    assert len(body["items"]) == 2
    assert body["pages"] == 2
    assert body["total"] == 3

    body = utils.get_json_ok(f"{LIST_URL}?per_page=2&keyword=org&page=2").json
    assert len(body["items"]) == 1


def test_list_page_out_of_range(client, seeder, utils):
    _create_org(seeder, "Alpha", verified=True)

    utils.assert_response_notFound(utils.get_json(f"{LIST_URL}?page=99"))


def test_list_per_page_too_large(client, utils):
    utils.assert_response_unprocessable_entity(
        utils.get_json(f"{LIST_URL}?per_page=1000")
    )


def test_list_includes_unverified_for_verifier(client, seeder, utils):
    _create_org(seeder, "Hidden")
    owner_id, _ = _create_org(
        seeder, "Verifier", email="verifier@test.de", can_verify_other=True
    )
    utils.login("verifier@test.de")

    assert "Hidden" in _names(utils.get_json_ok(LIST_URL).json)


def test_list_includes_unverified_for_platform_admin(client, seeder, utils):
    _create_org(seeder, "Hidden")
    seeder.create_user(email="admin@test.de", admin=True)
    utils.login("admin@test.de")

    assert "Hidden" in _names(utils.get_json_ok(LIST_URL).json)


def test_list_hides_unverified_for_regular_member(client, seeder, utils):
    _create_org(seeder, "Hidden")
    _create_org(seeder, "Member", email="member@test.de")
    utils.login("member@test.de")

    assert "Hidden" not in _names(utils.get_json_ok(LIST_URL).json)


# get


def test_get_anonymous(client, app, db, seeder, utils):
    from project.infrastructure.models import AdminUnit

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    image_id = seeder.upsert_default_image()
    with app.app_context():
        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.url = "https://org.test"
        admin_unit.email = "info@org.test"
        admin_unit.phone = "0123"
        admin_unit.fax = "0456"
        admin_unit.description = "Line 1\nLine 2"
        admin_unit.location.street = "Main St 1"
        admin_unit.logo_id = image_id
        db.session.commit()

    body = utils.get_json_ok(_url(admin_unit_id)).json

    assert body["id"] == admin_unit_id
    assert body["name"] == "Meine Crew"
    assert body["short_name"] == "meinecrew"
    assert body["url"] == "https://org.test"
    assert body["email"] == "info@org.test"
    assert body["phone"] == "0123"
    assert body["fax"] == "0456"
    assert body["description"] == "Line 1\nLine 2"
    assert body["is_verified"] is True
    assert body["location"] == {
        "street": "Main St 1",
        "postal_code": "12345",
        "city": "City",
    }
    assert f"/image/{image_id}" in body["logo_url"]
    assert "s=120" in body["logo_url"]
    assert body["ical_url"].startswith("http")
    assert body["ical_url"].endswith(f"/organizations/{admin_unit_id}/ical")
    assert body["relation"] is None


def test_get_without_location(client, app, db, seeder, utils):
    from project.infrastructure.models import AdminUnit

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    with app.app_context():
        location = db.session.get(AdminUnit, admin_unit_id).location
        location.postalCode = None
        location.city = None
        db.session.commit()

    body = utils.get_json_ok(_url(admin_unit_id)).json

    assert body["location"] is None
    assert body["logo_url"] is None


def test_get_not_found(client, utils):
    utils.assert_response_notFound(utils.get_json(_url(12345)))


# relation


def _login_verifier(seeder, utils):
    """Logs in as the owner of an organization that can verify others."""
    _, source_id = _create_org(
        seeder, "Verifier", email="verifier@test.de", can_verify_other=True
    )
    utils.login("verifier@test.de")
    return source_id


def test_get_relation_create(client, seeder, utils):
    source_id = _login_verifier(seeder, utils)
    _, target_id = _create_org(seeder, "Target", verified=True)

    relation = utils.get_json_ok(_url(target_id)).json["relation"]

    assert relation["source"] == {"id": source_id, "name": "Verifier"}
    assert relation["relation_id"] is None
    assert relation["edit_url"] is None
    assert relation["create_url"].endswith(
        f"/manage/admin_unit/{source_id}/outgoing_organization_relation/create"
        f"?target={target_id}&verify=1"
    )


def test_get_relation_existing(client, seeder, utils):
    source_id = _login_verifier(seeder, utils)
    _, target_id = _create_org(seeder, "Target", verified=True)
    relation_id = seeder.create_admin_unit_relation(
        source_id, target_id, auto_verify_event_reference_requests=True, verify=True
    )

    relation = utils.get_json_ok(_url(target_id)).json["relation"]

    assert relation["relation_id"] == relation_id
    assert relation["verify"] is True
    assert relation["auto_verify_event_reference_requests"] is True
    assert relation["create_url"] is None
    assert relation["edit_url"].endswith(
        f"/manage/admin_unit/{source_id}/outgoing_organization_relation/{relation_id}/update"
    )


def test_get_relation_for_unverified_target(client, seeder, utils):
    _login_verifier(seeder, utils)
    _, target_id = _create_org(seeder, "Target")

    body = utils.get_json_ok(_url(target_id)).json

    assert body["is_verified"] is False
    assert body["relation"]["create_url"]


def test_get_relation_none_for_own_organization(client, seeder, utils):
    source_id = _login_verifier(seeder, utils)

    assert utils.get_json_ok(_url(source_id)).json["relation"] is None


def test_get_relation_none_without_write_permission(client, seeder, utils):
    _, source_id = _create_org(
        seeder, "Verifier", email="owner@test.de", can_verify_other=True
    )
    seeder.create_admin_unit_member(
        source_id, ["event_verifier"], email="member@test.de"
    )
    _, target_id = _create_org(seeder, "Target", verified=True)
    utils.login("member@test.de")

    assert utils.get_json_ok(_url(target_id)).json["relation"] is None


def test_get_relation_none_if_source_cannot_use_relations(client, seeder, utils):
    _, source_id = _create_org(
        seeder,
        "Plain",
        email="plain@test.de",
        incoming_reference_requests_allowed=False,
    )
    _, target_id = _create_org(seeder, "Target", verified=True)
    utils.login("plain@test.de")

    assert utils.get_json_ok(_url(target_id)).json["relation"] is None


def test_get_relation_with_reference_requests_allowed(client, seeder, utils):
    # Not a verifier, but accepts reference requests: still gets the card.
    _, source_id = _create_org(seeder, "Plain", email="plain@test.de")
    _, target_id = _create_org(seeder, "Target", verified=True)
    utils.login("plain@test.de")

    assert utils.get_json_ok(_url(target_id)).json["relation"]["create_url"]


def test_get_relation_none_for_user_without_organization(client, seeder, utils):
    _, target_id = _create_org(seeder, "Target", verified=True)
    seeder.create_user(email="lonely@test.de")
    utils.login("lonely@test.de")

    assert utils.get_json_ok(_url(target_id)).json["relation"] is None
