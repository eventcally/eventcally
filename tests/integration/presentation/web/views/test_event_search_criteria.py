"""Event search form data → query criteria."""

from project.presentation.web.views.event_search_criteria import (
    criteria_from_search_params,
)
from project.presentation.web.views.event_search_params import EventSearchParams
from project.shared.dateutils import create_berlin_date


def test_empty_form_data_is_an_empty_search():
    criteria = criteria_from_search_params(EventSearchParams())

    assert criteria.category_ids == []
    assert criteria.tags == []
    assert criteria.keyword is None
    assert criteria.exclude_recurring is False


def test_single_values_become_one_element_lists():
    params = EventSearchParams()
    params.date_from = create_berlin_date(2040, 1, 1)
    params.keyword = "Jam"
    params.category_id = 3
    params.tag = "music"
    params.postal_code = "386"
    params.weekday = [1, 2]
    params.latitude = "51.9"
    params.longitude = "10.4"
    params.distance = 500
    params.exclude_recurring = True
    params.expected_participants_min = 10

    criteria = criteria_from_search_params(params, admin_unit_id=4)

    assert criteria.date_from == create_berlin_date(2040, 1, 1)
    assert criteria.keyword == "Jam"
    assert criteria.category_ids == [3]
    assert criteria.tags == ["music"]
    assert criteria.postal_codes == ["386"]
    assert criteria.weekdays == [1, 2]
    assert (criteria.latitude, criteria.longitude, criteria.distance) == (
        51.9,
        10.4,
        500,
    )
    assert criteria.exclude_recurring is True
    assert criteria.expected_participants_min == 10
    assert criteria.admin_unit_id == 4


def test_the_blank_category_choice_is_no_category():
    params = EventSearchParams()
    params.category_id = 0

    assert criteria_from_search_params(params).category_ids == []
