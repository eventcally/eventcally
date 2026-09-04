# Single source of truth: env token -> derived app.config boolean key.
# Opt-out semantics: token present => that feature's *_ENABLED key is False.
# Add a future flag by adding one entry here.
FEATURE_FLAGS = {
    "EventListsDisabled": "FEATURE_EVENT_LISTS_ENABLED",
    "UserFavoritesDisabled": "FEATURE_USER_FAVORITES_ENABLED",
    "ApiEventDateDisabled": "FEATURE_API_EVENT_DATE_ENABLED",
    "ApiEventDatesDisabled": "FEATURE_API_EVENT_DATES_ENABLED",
    "ApiEventListDisabled": "FEATURE_API_EVENT_LIST_ENABLED",
}


def parse_feature_flags(raw: str | None) -> set[str]:
    """Return the set of *known* active tokens from a comma-separated string.

    Unknown tokens are ignored so a newer env config never crashes an older image.
    """
    return {
        token
        for token in (t.strip() for t in (raw or "").split(","))
        if token in FEATURE_FLAGS
    }


def apply_feature_flags_to_config(config, raw: str | None) -> None:
    active = parse_feature_flags(raw)
    config["FEATURE_FLAGS"] = active
    for token, config_key in FEATURE_FLAGS.items():  # every feature defaults ENABLED
        config[config_key] = token not in active
