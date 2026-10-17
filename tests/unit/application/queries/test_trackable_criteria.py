from datetime import datetime

import pytest
from pydantic import ValidationError

from project.application.queries import PageRequest, TrackableCriteria


def test_trackable_criteria_defaults_to_no_bounds():
    criteria = TrackableCriteria()

    assert criteria.model_dump() == {
        "created_at_from": None,
        "created_at_to": None,
        "updated_at_from": None,
        "updated_at_to": None,
        "last_modified_at_from": None,
        "last_modified_at_to": None,
    }


def test_last_modified_at_to_is_independent_of_created_at_to():
    # TrackableSearchParams.load_from_request defaulted last_modified_at_to from
    # created_at_to; the criteria must keep the two bounds apart.
    created_at_to = datetime(2026, 1, 1)

    criteria = TrackableCriteria(created_at_to=created_at_to)

    assert criteria.created_at_to == created_at_to
    assert criteria.last_modified_at_to is None


def test_trackable_criteria_survives_strict_round_trip():
    criteria = TrackableCriteria(
        created_at_from=datetime(2026, 1, 1),
        last_modified_at_to=datetime(2026, 2, 1),
    )

    validated = TrackableCriteria.model_validate(
        criteria.model_dump(round_trip=True), strict=True
    )

    assert validated == criteria


def test_trackable_criteria_rejects_non_datetime():
    with pytest.raises(ValidationError):
        TrackableCriteria(created_at_from="yesterday")


def test_page_request_defaults():
    page_request = PageRequest()

    assert page_request.page == 1
    assert page_request.per_page == 20
    assert page_request.offset == 0


def test_page_request_offset():
    assert PageRequest(page=3, per_page=50).offset == 100


@pytest.mark.parametrize(
    "kwargs",
    [
        {"page": 0},
        {"page": -1},
        {"per_page": 0},
        {"per_page": 101},
    ],
)
def test_page_request_rejects_out_of_bounds(kwargs):
    with pytest.raises(ValidationError):
        PageRequest(**kwargs)


def test_page_request_allows_modular_list_page_size():
    assert PageRequest(per_page=50).per_page == 50
    assert PageRequest(per_page=100).per_page == 100
