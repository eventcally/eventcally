PLACES_URL = "/bff/public/places"


def test_suggestions_are_anonymous(client, utils, monkeypatch):
    from project.presentation.bff.public import places

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

    body = utils.get_json_ok(f"{PLACES_URL}?keyword=Goslar").json

    assert body["items"] == [
        {"gmaps_id": "abc", "text": "Goslar, Germany", "main_text": "Goslar"},
        {"gmaps_id": "def", "text": "Other", "main_text": None},
    ]


def test_blank_keyword_does_not_call_google(client, utils, monkeypatch):
    from project.presentation.bff.public import places

    def fail(keyword):  # pragma: no cover
        raise AssertionError("Google must not be called")

    monkeypatch.setattr(places, "find_gmaps_places", fail)

    assert utils.get_json_ok(f"{PLACES_URL}?keyword=%20%20").json == {"items": []}


def test_empty_keyword_is_422(client, utils):
    assert utils.get_json(f"{PLACES_URL}?keyword=").status_code == 422


def test_coordinate(client, utils, monkeypatch):
    from project.presentation.bff.public import places

    monkeypatch.setattr(
        places,
        "get_gmaps_place",
        lambda gmaps_id: {"geometry": {"location": {"lat": 51.9, "lng": 10.4}}},
    )

    assert utils.get_json_ok(f"{PLACES_URL}/abc/coordinate").json == {
        "latitude": 51.9,
        "longitude": 10.4,
    }


def test_coordinate_without_geometry_is_404(client, utils, monkeypatch):
    from project.presentation.bff.public import places

    monkeypatch.setattr(places, "get_gmaps_place", lambda gmaps_id: {})

    assert utils.get_json(f"{PLACES_URL}/abc/coordinate").status_code == 404


def test_rate_limited(client, utils, monkeypatch):
    from project.presentation.bff.public import places

    monkeypatch.setattr(places, "find_gmaps_places", lambda keyword: [])

    # The limit is shared with the other tests of this module, so count up to it.
    statuses = [
        utils.get_json(f"{PLACES_URL}?keyword=Goslar").status_code for _ in range(31)
    ]

    assert statuses[0] in (200, 429)
    assert 429 in statuses
    assert statuses[-1] == 429
