from project.application.queries import PageRequest, SearchEventDatesQuery
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.queries.page_request import MAX_PER_PAGE
from project.application.query_bus import QueryBus

PAGE_SIZE = MAX_PER_PAGE


def collect_event_dates(
    query_bus: QueryBus,
    criteria: EventSearchCriteria,
    max_dates: int,
    reference_admin_unit_id=None,
) -> tuple:
    """Up to `max_dates` event-date hits in search order and whether more exist."""
    hits = []
    page_number = 1

    while True:
        page = query_bus.handle(
            SearchEventDatesQuery(
                criteria=criteria,
                reference_admin_unit_id=reference_admin_unit_id,
                page=PageRequest(page=page_number, per_page=PAGE_SIZE),
            )
        )
        hits.extend(page.items)

        if not page.has_next or len(hits) >= max_dates:
            break

        page_number += 1

    return hits[:max_dates], page.total > max_dates
