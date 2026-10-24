PLACES_URL = "/bff/manage/places"


def test_suggestions(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(
        places,
        "find_gmaps_places",
        lambda keyword: [
            {
                "place_id": "abc",
                "description": f"{keyword}, Germany",
                "structured_formatting": {"main_text": keyword},
            },
            {"place_id": "def", "description": "Other"},
        ],
    )
    seeder.setup_base()

    body = utils.get_json_ok(f"{PLACES_URL}?keyword=Goslar").json

    assert body["items"] == [
        {"gmaps_id": "abc", "text": "Goslar, Germany", "main_text": "Goslar"},
        {"gmaps_id": "def", "text": "Other", "main_text": None},
    ]


def test_suggestions_empty_keyword_is_422(client, seeder, utils):
    seeder.setup_base()

    assert utils.get_json(f"{PLACES_URL}?keyword=").status_code == 422
    assert utils.get_json(PLACES_URL).status_code == 422


def test_coordinate(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(
        places,
        "get_gmaps_place",
        lambda gmaps_id: {"geometry": {"location": {"lat": 51.9, "lng": 10.4}}},
    )
    seeder.setup_base()

    body = utils.get_json_ok(f"{PLACES_URL}/abc/coordinate").json

    assert body == {"latitude": 51.9, "longitude": 10.4}


def test_coordinate_unknown_place_is_404(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(places, "get_gmaps_place", lambda gmaps_id: {})
    seeder.setup_base()

    assert utils.get_json(f"{PLACES_URL}/abc/coordinate").status_code == 404


def test_address(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(
        places,
        "get_gmaps_place",
        lambda gmaps_id: {
            "address_components": [
                {"types": ["street_number"], "long_name": "12"},
                {"types": ["route"], "long_name": "Markt"},
                {"types": ["locality"], "long_name": "Goslar"},
                {
                    "types": ["administrative_area_level_1"],
                    "long_name": "Niedersachsen",
                },
                {"types": ["postal_code"], "long_name": "38640"},
                {"types": ["country"], "long_name": "Deutschland"},
            ],
            "geometry": {"location": {"lat": 51.9, "lng": 10.4}},
        },
    )
    seeder.setup_base()

    body = utils.get_json_ok(f"{PLACES_URL}/abc/address").json

    assert body == {
        "street": "Markt 12",
        "postalCode": "38640",
        "city": "Goslar",
        "state": "Niedersachsen",
        "latitude": 51.9,
        "longitude": 10.4,
    }


def test_address_unknown_place_is_404(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(places, "get_gmaps_place", lambda gmaps_id: {})
    seeder.setup_base()

    assert utils.get_json(f"{PLACES_URL}/abc/address").status_code == 404


def test_address_without_permission_is_403(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import places

    monkeypatch.setattr(places, "can_use_manage_place_lookup", lambda: False)
    seeder.setup_base()

    assert utils.get_json(f"{PLACES_URL}/abc/address").status_code == 403


def test_member_without_planning_may_look_up_places(client, seeder, utils):
    seeder.setup_base(admin_unit_verified=False)

    assert utils.get_json(f"{PLACES_URL}?keyword=x").status_code == 200


def test_user_without_organization_may_look_up_places_to_create_one(
    client, seeder, utils
):
    seeder.create_user()
    utils.login()

    assert utils.get_json(f"{PLACES_URL}?keyword=x").status_code == 200


def test_user_without_organization_is_403_in_closed_phase(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.create_user()
    utils.login()

    assert utils.get_json(f"{PLACES_URL}?keyword=x").status_code == 403
    assert utils.get_json(f"{PLACES_URL}/abc/coordinate").status_code == 403


def test_invited_user_may_look_up_places_in_closed_phase(client, app, seeder, utils):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    seeder.create_admin_unit_invitation(admin_unit_id)
    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    assert utils.get_json(f"{PLACES_URL}?keyword=x").status_code == 200
