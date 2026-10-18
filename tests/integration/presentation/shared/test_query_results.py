import pytest


@pytest.mark.parametrize(
    "query_string, kwargs, expected",
    [
        ("", {}, (1, 20)),
        ("page=3&per_page=7", {}, (3, 7)),
        ("per_page=7", {"default_per_page": 50}, (1, 7)),
        ("", {"default_per_page": 50}, (1, 50)),
        ("page=2&per_page=7", {"per_page": 50}, (2, 50)),
        ("per_page=80", {"max_per_page": 50}, (1, 50)),
        ("per_page=1000", {}, (1, 100)),
    ],
)
def test_page_request_from_request_args(app, query_string, kwargs, expected):
    from project.presentation.shared.query_results import page_request_from_request_args

    with app.test_request_context(f"/?{query_string}"):
        page_request = page_request_from_request_args(**kwargs)

    assert (page_request.page, page_request.per_page) == expected


@pytest.mark.parametrize(
    "query_string", ["page=0", "page=-2", "page=abc", "per_page=0", "per_page=x"]
)
def test_page_request_from_request_args_aborts_on_invalid_values(app, query_string):
    from werkzeug.exceptions import NotFound

    from project.presentation.shared.query_results import page_request_from_request_args

    with app.test_request_context(f"/?{query_string}"):
        with pytest.raises(NotFound):
            page_request_from_request_args()


def test_abort_if_page_out_of_range():
    from werkzeug.exceptions import NotFound

    from project.application.read_models.page import Page
    from project.presentation.shared.query_results import abort_if_page_out_of_range

    abort_if_page_out_of_range(Page[int](items=[], page=1, per_page=20, total=0))
    abort_if_page_out_of_range(Page[int](items=[1], page=2, per_page=1, total=2))

    with pytest.raises(NotFound):
        abort_if_page_out_of_range(Page[int](items=[], page=2, per_page=20, total=3))


def test_result_or_404():
    from werkzeug.exceptions import NotFound

    from project.presentation.shared.query_results import result_or_404

    value = object()
    assert result_or_404(value) is value
    assert result_or_404(0) == 0
    assert result_or_404(False) is False

    with pytest.raises(NotFound):
        result_or_404(None)
