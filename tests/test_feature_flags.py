from project.feature_flags import (
    FEATURE_FLAGS,
    apply_feature_flags_to_config,
    parse_feature_flags,
)


def test_parse_feature_flags_empty():
    assert parse_feature_flags("") == set()


def test_parse_feature_flags_none():
    assert parse_feature_flags(None) == set()


def test_parse_feature_flags_whitespace():
    assert parse_feature_flags("   ") == set()


def test_parse_feature_flags_single_token():
    assert parse_feature_flags("ReferencedEventChangedDetailsDisabled") == {
        "ReferencedEventChangedDetailsDisabled"
    }


def test_parse_feature_flags_multiple_tokens_with_spaces_and_trailing_comma():
    result = parse_feature_flags(
        " ReferencedEventChangedDetailsDisabled , ApiEventDateDisabled, "
    )
    assert result == {"ReferencedEventChangedDetailsDisabled", "ApiEventDateDisabled"}


def test_parse_feature_flags_unknown_token_ignored():
    assert parse_feature_flags("BogusDisabled") == set()


def test_parse_feature_flags_mixed_known_and_unknown():
    result = parse_feature_flags("ReferencedEventChangedDetailsDisabled,BogusDisabled")
    assert result == {"ReferencedEventChangedDetailsDisabled"}


def test_apply_feature_flags_to_config_empty():
    config = {}
    apply_feature_flags_to_config(config, None)
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"] is True
    assert config["FEATURE_API_EVENT_DATE_ENABLED"] is True


def test_apply_feature_flags_to_config_both_disabled():
    config = {}
    apply_feature_flags_to_config(
        config, "ReferencedEventChangedDetailsDisabled,ApiEventDateDisabled"
    )
    assert config["FEATURE_FLAGS"] == {
        "ReferencedEventChangedDetailsDisabled",
        "ApiEventDateDisabled",
    }
    assert config["FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"] is False
    assert config["FEATURE_API_EVENT_DATE_ENABLED"] is False


def test_apply_feature_flags_to_config_unknown_token_ignored():
    config = {}
    apply_feature_flags_to_config(config, "BogusDisabled")
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"] is True


def test_feature_flags_registry_mapping():
    assert FEATURE_FLAGS["ApiEventDateDisabled"] == "FEATURE_API_EVENT_DATE_ENABLED"
    assert FEATURE_FLAGS["ApiEventDatesDisabled"] == "FEATURE_API_EVENT_DATES_ENABLED"
    assert FEATURE_FLAGS["ApiEventListDisabled"] == "FEATURE_API_EVENT_LIST_ENABLED"
    assert (
        FEATURE_FLAGS["ReferencedEventChangedDetailsDisabled"]
        == "FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"
    )


def test_apply_feature_flags_to_config_referenced_event_changed_details_disabled():
    config = {}
    apply_feature_flags_to_config(config, "ReferencedEventChangedDetailsDisabled")
    assert config["FEATURE_FLAGS"] == {"ReferencedEventChangedDetailsDisabled"}
    assert config["FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"] is False
    assert config["FEATURE_API_EVENT_DATE_ENABLED"] is True


def test_apply_feature_flags_to_config_api_endpoints_disabled():
    config = {}
    apply_feature_flags_to_config(
        config, "ApiEventDateDisabled,ApiEventDatesDisabled,ApiEventListDisabled"
    )
    assert config["FEATURE_API_EVENT_DATE_ENABLED"] is False
    assert config["FEATURE_API_EVENT_DATES_ENABLED"] is False
    assert config["FEATURE_API_EVENT_LIST_ENABLED"] is False
    assert config["FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED"] is True
