import pytest

from project.shared import feature_flags
from project.shared.feature_flags import (
    apply_feature_flags_to_config,
    parse_feature_flags,
)


@pytest.fixture
def fake_flag(monkeypatch):
    monkeypatch.setattr(
        feature_flags,
        "FEATURE_FLAGS",
        {"FakeFeatureDisabled": "FEATURE_FAKE_ENABLED"},
    )


def test_parse_feature_flags_empty():
    assert parse_feature_flags("") == set()


def test_parse_feature_flags_none():
    assert parse_feature_flags(None) == set()


def test_parse_feature_flags_whitespace():
    assert parse_feature_flags("   ") == set()


def test_parse_feature_flags_single_token(fake_flag):
    assert parse_feature_flags("FakeFeatureDisabled") == {"FakeFeatureDisabled"}


def test_parse_feature_flags_multiple_tokens_with_spaces_and_trailing_comma(fake_flag):
    result = parse_feature_flags(" FakeFeatureDisabled , BogusDisabled, ")
    assert result == {"FakeFeatureDisabled"}


def test_parse_feature_flags_unknown_token_ignored():
    assert parse_feature_flags("BogusDisabled") == set()


def test_parse_feature_flags_mixed_known_and_unknown(fake_flag):
    result = parse_feature_flags("FakeFeatureDisabled,BogusDisabled")
    assert result == {"FakeFeatureDisabled"}


def test_apply_feature_flags_to_config_empty(fake_flag):
    config = {}
    apply_feature_flags_to_config(config, None)
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_FAKE_ENABLED"] is True


def test_apply_feature_flags_to_config_unknown_token_ignored(fake_flag):
    config = {}
    apply_feature_flags_to_config(config, "BogusDisabled")
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_FAKE_ENABLED"] is True


def test_feature_flags_registry_is_empty():
    assert feature_flags.FEATURE_FLAGS == {}


def test_apply_feature_flags_to_config_disabled(fake_flag):
    config = {}
    apply_feature_flags_to_config(config, "FakeFeatureDisabled")
    assert config["FEATURE_FLAGS"] == {"FakeFeatureDisabled"}
    assert config["FEATURE_FAKE_ENABLED"] is False


def test_retired_tokens_are_ignored():
    raw = (
        "ApiEventDateDisabled,ApiEventDatesDisabled,ApiEventListDisabled,"
        "ReferencedEventChangedDetailsDisabled"
    )
    assert parse_feature_flags(raw) == set()

    config = {}
    apply_feature_flags_to_config(config, raw)
    assert "FEATURE_API_EVENT_DATE_ENABLED" not in config
    assert "FEATURE_API_EVENT_DATES_ENABLED" not in config
    assert "FEATURE_API_EVENT_LIST_ENABLED" not in config
    assert "FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED" not in config
