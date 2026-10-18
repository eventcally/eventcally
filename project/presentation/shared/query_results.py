from flask import abort, request

from project.application.queries.page_request import (
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
    PageRequest,
)
from project.application.read_models.page import Page


def page_request_from_request_args(
    per_page: int | None = None,
    default_per_page: int = DEFAULT_PER_PAGE,
    max_per_page: int | None = None,
) -> PageRequest:
    """Read `page` (and `per_page` unless given) from the query string.

    Mirrors Flask-SQLAlchemy's `paginate()` with `error_out=True`: invalid or
    non-positive values abort with 404, `max_per_page` clamps.
    """
    try:
        page = int(request.args.get("page", 1))

        if per_page is None:
            per_page = int(request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        abort(404)

    if max_per_page is not None:
        per_page = min(per_page, max_per_page)

    if page < 1 or per_page < 1:
        abort(404)

    return PageRequest(page=page, per_page=min(per_page, MAX_PER_PAGE))


def abort_if_page_out_of_range(page: Page):
    """404 for an empty page beyond the first, like `paginate(error_out=True)`."""
    if page.is_out_of_range:
        abort(404)


def result_or_404(value):
    """Single-object queries return None when nothing is found."""
    if value is None:
        abort(404)

    return value
