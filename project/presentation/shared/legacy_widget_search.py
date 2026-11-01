from typing import Optional, Protocol

from project.application.queries import ListAllEventCategoriesQuery
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.query_bus import QueryBus
from project.shared.dateutils import date_set_end_of_day, form_input_to_date, get_today


class LegacyWidgetFilters(Protocol):
    """The filters of the iframe widget page `/organizations/<id>/widget/eventdates`."""

    date_from: Optional[str]
    date_to: Optional[str]
    keyword: Optional[str]
    category_id: Optional[str]
    tag: Optional[str]


class _InvalidFilter(ValueError):
    pass


def _parse_date(value: Optional[str], end_of_day: bool = False):
    """The part before a space or `T`, as `YYYY-MM-DD` (the old `CustomDateField`)."""
    if not value:
        return None

    try:
        date = form_input_to_date(value.split(" ")[0].split("T")[0])
    except ValueError:
        raise _InvalidFilter()

    return date_set_end_of_day(date) if end_of_day else date


def _parse_category(value: Optional[str], category_ids: set) -> int:
    if not value:
        return 0

    try:
        category_id = int(value)
    except ValueError:
        raise _InvalidFilter()

    if category_id and category_id not in category_ids:
        raise _InvalidFilter()

    return category_id


def legacy_widget_criteria(
    query_bus: QueryBus, organization_id: int, filters: LegacyWidgetFilters
) -> EventSearchCriteria:
    """The search of the iframe widget page that customers embed. Its WTForms form was
    all or nothing: one invalid field (a date, a category that does not exist) and every
    filter fell back to the defaults (from today, nothing else). A date sent empty meant
    no bound; a date not sent at all meant today. Planned events are not included."""
    date_from = get_today()
    date_to = None
    keyword = None
    category_id = 0
    tag = None

    try:
        category_ids = {c.id for c in query_bus.handle(ListAllEventCategoriesQuery())}
        parsed_from = (
            date_from if filters.date_from is None else _parse_date(filters.date_from)
        )
        parsed_to = _parse_date(filters.date_to, end_of_day=True)
        parsed_category = _parse_category(filters.category_id, category_ids)
        date_from, date_to, category_id = parsed_from, parsed_to, parsed_category
        keyword = filters.keyword or None
        tag = filters.tag or None
    except _InvalidFilter:
        pass

    return EventSearchCriteria(
        date_from=date_from,
        date_to=date_to,
        keyword=keyword,
        category_ids=[category_id] if category_id else [],
        tags=[tag] if tag else [],
        admin_unit_id=organization_id,
        include_admin_unit_references=True,
    )
