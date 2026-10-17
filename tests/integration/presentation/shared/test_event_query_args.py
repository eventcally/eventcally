"""The request → `EventSearchCriteria` mapping of the event searches."""

from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.shared.dateutils import create_berlin_date


def _criteria(app, query, kwargs=None, **options):
    with app.test_request_context(f"/?{query}"):
        return event_search_criteria_from_request(kwargs or {}, **options)


def test_empty_request_is_an_empty_search(app):
    criteria = _criteria(app, "")

    assert criteria.keyword is None
    assert criteria.category_ids == []
    assert criteria.sort is None
    assert criteria.include_private is False


def test_lists_are_repeated_or_comma_separated_and_drop_zero(app):
    criteria = _criteria(
        app,
        "category_id=1&category_id=3&custom_category_set_id=4,5,0"
        "&postal_code=386,38&tag=a&tag=b&internal_tag=x&weekday=1&weekday=2",
    )

    assert criteria.category_ids == [1, 3]
    assert criteria.custom_category_set_ids == [4, 5]
    assert criteria.postal_codes == ["386", "38"]
    assert criteria.tags == ["a", "b"]
    assert criteria.internal_tags == ["x"]
    assert criteria.weekdays == [1, 2]


def test_scalars_dates_and_coordinates(app):
    criteria = _criteria(
        app,
        "keyword=Jam&date_from=2040-03-01&date_to=2040-03-02&coordinate=51.9,10.4"
        "&distance=500&organizer_id=3&event_place_id=4&expected_participants_min=10"
        "&organization_id=7",
    )

    assert criteria.keyword == "Jam"
    assert criteria.date_from == create_berlin_date(2040, 3, 1)
    assert criteria.date_to == create_berlin_date(2040, 3, 2, 23, 59, 59)
    assert (criteria.latitude, criteria.longitude) == (51.9, 10.4)
    assert criteria.distance == 500
    assert criteria.organizer_id == 3
    assert criteria.event_place_id == 4
    assert criteria.expected_participants_min == 10
    assert criteria.admin_unit_id == 7


def test_stati_ignore_unknown_names(app):
    criteria = _criteria(
        app, "status=cancelled&status=nonsense&public_status=draft,published"
    )

    assert criteria.status == [EventStatus.cancelled]
    assert criteria.public_status == [
        EventPublicStatus.draft,
        EventPublicStatus.published,
    ]


def test_booleans(app):
    criteria = _criteria(
        app,
        "exclude_recurring=true&include_organization_references=1"
        "&organization_references_only=no",
    )

    assert criteria.exclude_recurring is True
    assert criteria.include_admin_unit_references is True
    assert criteria.admin_unit_references_only is False


def test_audit_bounds_and_sort_come_from_the_validated_kwargs(app):
    criteria = _criteria(
        app,
        "",
        {"sort": "-rating", "created_at_from": create_berlin_date(2026, 1, 1)},
    )

    assert criteria.sort.value == "-rating"
    assert criteria.trackable.created_at_from == create_berlin_date(2026, 1, 1)


def test_defaults_yield_to_the_request_and_overrides_win(app):
    defaults = dict(include_admin_unit_references=True, admin_unit_id=1)

    criteria = _criteria(
        app, "include_organization_references=0&admin_unit_id=2", defaults=defaults
    )
    assert criteria.include_admin_unit_references is False
    assert criteria.admin_unit_id == 2

    criteria = _criteria(app, "admin_unit_id=2", defaults=defaults, admin_unit_id=9)
    assert criteria.include_admin_unit_references is True
    assert criteria.admin_unit_id == 9


def test_no_reference_organization_for_anonymous_callers(app):
    with app.test_request_context("/"):
        assert reference_admin_unit_id_for_api() is None
