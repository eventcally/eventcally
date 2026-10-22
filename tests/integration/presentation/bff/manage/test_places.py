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
