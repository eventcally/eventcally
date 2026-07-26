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
    assert parse_feature_flags("EventListsDisabled") == {"EventListsDisabled"}


def test_parse_feature_flags_multiple_tokens_with_spaces_and_trailing_comma():
    result = parse_feature_flags(" EventListsDisabled , UserFavoritesDisabled, ")
    assert result == {"EventListsDisabled", "UserFavoritesDisabled"}


def test_parse_feature_flags_unknown_token_ignored():
    assert parse_feature_flags("BogusDisabled") == set()


def test_parse_feature_flags_mixed_known_and_unknown():
    result = parse_feature_flags("EventListsDisabled,BogusDisabled")
    assert result == {"EventListsDisabled"}


def test_apply_feature_flags_to_config_empty():
    config = {}
    apply_feature_flags_to_config(config, None)
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_EVENT_LISTS_ENABLED"] is True
    assert config["FEATURE_USER_FAVORITES_ENABLED"] is True


def test_apply_feature_flags_to_config_event_lists_disabled():
    config = {}
    apply_feature_flags_to_config(config, "EventListsDisabled")
    assert config["FEATURE_FLAGS"] == {"EventListsDisabled"}
    assert config["FEATURE_EVENT_LISTS_ENABLED"] is False
    assert config["FEATURE_USER_FAVORITES_ENABLED"] is True


def test_apply_feature_flags_to_config_both_disabled():
    config = {}
    apply_feature_flags_to_config(config, "EventListsDisabled,UserFavoritesDisabled")
    assert config["FEATURE_FLAGS"] == {
        "EventListsDisabled",
        "UserFavoritesDisabled",
    }
    assert config["FEATURE_EVENT_LISTS_ENABLED"] is False
    assert config["FEATURE_USER_FAVORITES_ENABLED"] is False


def test_apply_feature_flags_to_config_unknown_token_ignored():
    config = {}
    apply_feature_flags_to_config(config, "BogusDisabled")
    assert config["FEATURE_FLAGS"] == set()
    assert config["FEATURE_EVENT_LISTS_ENABLED"] is True
    assert config["FEATURE_USER_FAVORITES_ENABLED"] is True


def test_feature_flags_registry_mapping():
    assert FEATURE_FLAGS["EventListsDisabled"] == "FEATURE_EVENT_LISTS_ENABLED"
    assert FEATURE_FLAGS["UserFavoritesDisabled"] == "FEATURE_USER_FAVORITES_ENABLED"
