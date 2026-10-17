"""Building blocks shared by the query-side SQLAlchemy read repositories."""

from typing import Callable, TypeVar

from sqlalchemy import Select, func, select

from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.page import Page

T = TypeVar("T")


def trackable_filters(model, criteria: TrackableCriteria) -> list:
    """`_from` bounds are inclusive, `_to` bounds exclusive."""
    bounds = [
        (model.created_at, criteria.created_at_from, criteria.created_at_to),
        (model.updated_at, criteria.updated_at_from, criteria.updated_at_to),
        (
            model.last_modified_at,
            criteria.last_modified_at_from,
            criteria.last_modified_at_to,
        ),
    ]
    filters = []

    for column, lower, upper in bounds:
        if lower:
            filters.append(column >= lower)

        if upper:
            filters.append(column < upper)

    return filters


def count(session, stmt: Select) -> int:
    """Count the rows of `stmt`, ignoring its ordering."""
    subquery = stmt.order_by(None).subquery()
    return session.execute(select(func.count()).select_from(subquery)).scalar_one()


def paginate(
    session,
    stmt: Select,
    count_stmt: Select,
    page_request: PageRequest,
    to_item: Callable[..., T],
) -> Page[T]:
    """Run one page of `stmt` and map each row with `to_item(row)`."""
    rows = session.execute(
        stmt.limit(page_request.per_page).offset(page_request.offset)
    ).all()

    return Page[T](
        items=[to_item(row) for row in rows],
        page=page_request.page,
        per_page=page_request.per_page,
        total=count(session, count_stmt),
    )


def trackable_order(model, sort) -> list:
    """Order clauses of an API `TrackableSort` (empty for `None`), as the legacy
    `TrackableSearchParams.get_trackable_order_by`."""
    if sort == TrackableSort.created_at_desc:
        return [model.created_at.desc()]

    if sort == TrackableSort.updated_at_desc:
        return [model.updated_at.desc().nulls_last()]

    if sort == TrackableSort.last_modified_at_desc:
        return [model.last_modified_at.desc()]

    return []
