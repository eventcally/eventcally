import os
from enum import Enum
from types import SimpleNamespace

import pytest
from psycopg2.errorcodes import CHECK_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import IntegrityError

from project.shared import utils


def _location(street=None, postal_code=None, city=None):
    return SimpleNamespace(street=street, postalCode=postal_code, city=city)


def test_strings_are_equal_ignoring_case():
    assert utils.strings_are_equal_ignoring_case("Straße", "STRASSE")
    assert not utils.strings_are_equal_ignoring_case("a", "b")
    assert not utils.strings_are_equal_ignoring_case("a", "")
    assert not utils.strings_are_equal_ignoring_case(None, "a")


def test_get_event_category_name():
    category = SimpleNamespace(name="Art")
    assert str(utils.get_event_category_name(category)) == "Event_Art"


def test_get_localized_enum_name():
    class Color(Enum):
        red = 1

    assert str(utils.get_localized_enum_name(Color.red)) == "Color.red"
    assert str(utils.get_localized_enum_name(Color.red, "Other")) == "Other.red"


def test_get_localized_scope():
    assert str(utils.get_localized_scope("event:read")) == "Scope_event:read"


def test_get_location_str_none():
    assert utils.get_location_str(None) == ""


def test_get_location_str_empty():
    assert utils.get_location_str(_location()) == ""


def test_get_location_str_full():
    location = _location("Strasse", "PLZ", "Ort")
    assert utils.get_location_str(location) == "Strasse, PLZ Ort"


def test_get_location_str_no_street():
    assert utils.get_location_str(_location(None, "PLZ", "Ort")) == "PLZ Ort"


def test_get_location_str_blank_street_and_only_city():
    assert utils.get_location_str(_location("  ", "", "Ort")) == "Ort"
    assert utils.get_location_str(_location("  ", "", "")) == ""


def test_get_place_str_none():
    assert utils.get_place_str(None) == ""


def test_get_place_str_no_location():
    assert utils.get_place_str(SimpleNamespace(name="Name", location=None)) == "Name"


def test_get_place_str_full():
    place = SimpleNamespace(name="Name", location=_location("Strasse", "PLZ", "Ort"))
    assert utils.get_place_str(place) == "Name, Strasse, PLZ Ort"


def test_make_dir(tmp_path):
    path = tmp_path / "a" / "b"
    utils.make_dir(path)
    utils.make_dir(path)  # existing directory is fine
    assert path.is_dir()


def test_clear_files_in_dir(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "link").symlink_to(tmp_path / "file.txt")
    (tmp_path / "sub").mkdir()

    utils.clear_files_in_dir(tmp_path)

    assert os.listdir(tmp_path) == ["sub"]


def test_clear_files_in_dir_missing_dir(tmp_path):
    utils.clear_files_in_dir(tmp_path / "missing")


def test_split_by_crlf():
    assert utils.split_by_crlf("a\r\n\r\nb\nc") == ["a", "b", "c"]
    assert utils.split_by_crlf("") == []


def test_make_check_violation():
    error = utils.make_check_violation("msg", "SELECT 1")
    assert isinstance(error, IntegrityError)
    assert error.orig.pgcode == CHECK_VIOLATION
    assert error.orig.message == "msg"
    assert error.statement == "SELECT 1"


def test_make_unique_violation():
    error = utils.make_unique_violation("dup")
    assert error.orig.pgcode == UNIQUE_VIOLATION
    assert error.orig.message == "dup"


def test_decode_response_content():
    response = SimpleNamespace(content="Grüße".encode("UTF-8"))
    assert utils.decode_response_content(response) == "Grüße"


def test_snake_case_to_human():
    assert utils.snake_case_to_human("event_place") == "Event place"
    assert utils.snake_case_to_human("") == ""


@pytest.mark.parametrize(
    "class_name,expected",
    [
        ("EventPlace", "event_place"),
        ("AdminUnit", "admin_unit"),
        ("OAuth2Client", "oauth2_client"),
        ("XRay", "xray"),
    ],
)
def test_class_name_to_model_name(class_name, expected):
    assert utils.class_name_to_model_name(class_name) == expected


@pytest.mark.parametrize(
    "model_name,expected",
    [
        ("settings", "settings"),
        ("event", "events"),
        ("api_key", "api_keys"),
        ("category", "categories"),
    ],
)
def test_model_name_to_plural(model_name, expected):
    assert utils.model_name_to_plural(model_name) == expected


def test_getattr_keypath():
    obj = SimpleNamespace(a=SimpleNamespace(b=5))
    assert utils.getattr_keypath(obj, "a.b") == 5
    assert utils.getattr_keypath(obj, "a.missing", "fallback") == "fallback"


@pytest.mark.parametrize(
    "term,expected",
    [("^abc", "abc%"), ("=abc", "abc"), ("abc", "%abc%")],
)
def test_parse_like_term(term, expected):
    assert utils.parse_like_term(term) == expected


def test_generate_api_key():
    assert len(utils.generate_api_key()) == 32
    assert utils.generate_api_key() != utils.generate_api_key()


def test_hash_api_key(monkeypatch):
    monkeypatch.setattr(
        "flask_security.utils.get_hmac", lambda key: b"h:" + key.encode()
    )
    assert utils.hash_api_key("secret") == "h:secret"


@pytest.mark.parametrize(
    "value,expected",
    [("true", True), ("Yes", True), ("1", True), ("off", False), ("", False)],
)
def test_str_to_bool(value, expected):
    assert utils.str_to_bool(value) is expected
