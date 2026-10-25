import pytest
from flask import Flask

from project.presentation.shared import maputils


class _FakeGmaps:
    def __init__(self, places=None, place=None, error=None):
        self._places = places or []
        self._place = place
        self._error = error

    def places_autocomplete_query(self, query, **kwargs):
        if self._error:
            raise self._error
        return self._places

    def place(self, gmaps_id, **kwargs):
        if self._error:
            raise self._error
        return self._place


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["GOOGLE_MAPS_API_KEY"] = None
    return app


@pytest.fixture(autouse=True)
def reset_gmaps(monkeypatch):
    monkeypatch.setattr(maputils, "google_maps_api_key", None)
    monkeypatch.setattr(maputils, "gmaps", None)


def test_init_without_key_leaves_no_client(app):
    with app.app_context():
        assert maputils.find_gmaps_places("x") == []
        assert maputils.get_gmaps_place("x") == {}

    assert maputils.gmaps is None


def test_init_with_key_creates_client_once(app, monkeypatch):
    created = []
    monkeypatch.setattr(
        maputils.googlemaps, "Client", lambda key: created.append(key) or "client"
    )
    app.config["GOOGLE_MAPS_API_KEY"] = "secret"

    with app.app_context():
        maputils._init_gmaps()
        maputils._init_gmaps()

    assert created == ["secret"]
    assert maputils.gmaps == "client"


def test_find_gmaps_places_keeps_only_places_with_id(app, monkeypatch):
    monkeypatch.setattr(maputils, "google_maps_api_key", "k")
    monkeypatch.setattr(
        maputils, "gmaps", _FakeGmaps(places=[{"place_id": "a"}, {"name": "b"}])
    )

    with app.app_context():
        assert maputils.find_gmaps_places("x") == [{"place_id": "a"}]


def test_get_gmaps_place_returns_result_only_when_ok(app, monkeypatch):
    monkeypatch.setattr(maputils, "google_maps_api_key", "k")

    with app.app_context():
        monkeypatch.setattr(
            maputils,
            "gmaps",
            _FakeGmaps(place={"status": "OK", "result": {"name": "n"}}),
        )
        assert maputils.get_gmaps_place("x") == {"name": "n"}

        monkeypatch.setattr(
            maputils, "gmaps", _FakeGmaps(place={"status": "NOT_FOUND"})
        )
        assert maputils.get_gmaps_place("x") == {}


def test_get_gmaps_place_address_maps_components():
    address = maputils.get_gmaps_place_address(
        {
            "address_components": [
                {"types": ["street_number"], "long_name": "5"},
                {"types": ["route"], "long_name": "Hauptstr."},
                {"types": ["locality"], "long_name": "Goslar"},
                {"types": ["administrative_area_level_1"], "long_name": "NDS"},
                {"types": ["postal_code"], "long_name": "38640"},
                {"types": ["country"], "long_name": "Deutschland"},
            ],
            "geometry": {"location": {"lat": 1.5, "lng": 2.5}},
        }
    )

    assert address == {
        "street": "Hauptstr. 5",
        "city": "Goslar",
        "state": "NDS",
        "postalCode": "38640",
        "latitude": 1.5,
        "longitude": 2.5,
    }
