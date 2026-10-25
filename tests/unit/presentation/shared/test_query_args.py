from enum import Enum

from flask import Flask

from project.application.queries import TrackableSort
from project.presentation.shared import query_args


class _Color(Enum):
    red = "red"


def test_page_request_from_kwargs_defaults_and_values():
    assert query_args.page_request_from_kwargs({}).page == 1
    assert query_args.page_request_from_kwargs({}).per_page == 20

    request = query_args.page_request_from_kwargs({"page": 3, "per_page": 5})
    assert (request.page, request.per_page) == (3, 5)


def test_trackable_criteria_from_kwargs_keeps_only_given_keys():
    criteria = query_args.trackable_criteria_from_kwargs(
        {"created_at_from": "2030-01-01T00:00:00", "updated_at_to": None, "other": 1}
    )

    assert criteria.created_at_from.year == 2030
    assert criteria.updated_at_to is None


def test_trackable_sort_from_kwargs():
    assert query_args.trackable_sort_from_kwargs({}) is None
    assert (
        query_args.trackable_sort_from_kwargs({"sort": "-created_at"})
        == TrackableSort.created_at_desc
    )


def test_enum_or_none():
    assert query_args.enum_or_none(_Color, "red") is _Color.red
    assert query_args.enum_or_none(_Color, "blue") is None


def test_list_arg_from_request():
    app = Flask(__name__)

    with app.test_request_context("/?a=1&a=0&a=2"):
        assert query_args.list_arg_from_request("a") == ["1", "2"]

    with app.test_request_context("/?a=1, 0,3"):
        assert query_args.list_arg_from_request("a") == ["1", "3"]

    with app.test_request_context("/"):
        assert query_args.list_arg_from_request("a") == []
