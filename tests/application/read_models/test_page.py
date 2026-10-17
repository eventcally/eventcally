"""Page[T] must paginate exactly like Flask-SQLAlchemy's Pagination.

The oracle is hand-written: tests/application must not import Flask-SQLAlchemy.
Pagination defines pages = ceil(total / per_page) (0 when total is 0),
has_prev = page > 1, has_next = page < pages, prev_num / next_num None when absent.
"""

import pytest

from project.application.read_models.page import Page

# (total, per_page) -> pages
EXPECTED_PAGES = {
    (0, 1): 0,
    (0, 20): 0,
    (0, 50): 0,
    (1, 1): 1,
    (1, 20): 1,
    (1, 50): 1,
    (20, 1): 20,
    (20, 20): 1,
    (20, 50): 1,
    (21, 1): 21,
    (21, 20): 2,
    (21, 50): 1,
    (100, 1): 100,
    (100, 20): 5,
    (100, 50): 2,
}

CASES = [
    (total, page, per_page, pages)
    for (total, per_page), pages in EXPECTED_PAGES.items()
    for page in (1, 2, 5)
]


def _items_on_page(total, page, per_page):
    start = (page - 1) * per_page
    return list(range(start, min(start + per_page, total)))


@pytest.mark.parametrize("total, page, per_page, pages", CASES)
def test_matches_flask_sqlalchemy_pagination(total, page, per_page, pages):
    result = Page[int](
        items=_items_on_page(total, page, per_page),
        page=page,
        per_page=per_page,
        total=total,
    )

    assert result.pages == pages
    assert result.has_prev == (page > 1)
    assert result.prev_num == (page - 1 if page > 1 else None)
    assert result.has_next == (page < pages)
    assert result.next_num == (page + 1 if page < pages else None)


@pytest.mark.parametrize(
    "total, page, per_page, expected",
    [
        (0, 1, 20, False),  # first page is never out of range, even when empty
        (20, 1, 20, False),
        (21, 2, 20, False),
        (20, 2, 20, True),
        (100, 5, 20, False),
        (100, 6, 20, True),
    ],
)
def test_is_out_of_range(total, page, per_page, expected):
    result = Page[int](
        items=_items_on_page(total, page, per_page),
        page=page,
        per_page=per_page,
        total=total,
    )

    assert result.is_out_of_range is expected


def test_is_frozen():
    result = Page[int](items=[1], page=1, per_page=20, total=1)

    with pytest.raises(Exception):
        result.total = 2


def test_properties_are_not_serialized():
    result = Page[int](items=[1, 2], page=1, per_page=20, total=2)

    assert result.model_dump() == {
        "items": [1, 2],
        "page": 1,
        "per_page": 20,
        "total": 2,
    }


def test_validates_item_type():
    with pytest.raises(Exception):
        Page[int](items=["not an int"], page=1, per_page=20, total=1)
