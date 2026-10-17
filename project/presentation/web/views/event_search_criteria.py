from project.application.queries import EventSearchCriteria


def _as_list(value) -> list:
    if value is None or value == "":
        return []

    return list(value) if isinstance(value, (list, tuple)) else [value]


def criteria_from_search_params(params, **overrides) -> EventSearchCriteria:
    """The event search form data (`EventSearchParams`, as filled by the forms) as
    query criteria. A single value is a one-element list, as the legacy filter."""
    values = dict(
        date_from=params.date_from,
        date_to=params.date_to,
        keyword=params.keyword or None,
        category_ids=[i for i in _as_list(params.category_id) if i],
        custom_category_set_ids=_as_list(params.custom_category_set_id),
        organizer_id=params.organizer_id or None,
        event_place_id=params.event_place_id or None,
        latitude=params.latitude or None,
        longitude=params.longitude or None,
        distance=params.distance or None,
        postal_codes=_as_list(params.postal_code),
        tags=_as_list(params.tag),
        internal_tags=_as_list(params.internal_tag),
        weekdays=_as_list(params.weekday),
        exclude_recurring=bool(params.exclude_recurring),
        expected_participants_min=params.expected_participants_min or None,
    )
    values.update(overrides)
    return EventSearchCriteria(**values)
