from dependency_injector.wiring import Provide, inject

from project.application.queries import (
    ListAllEventCategoriesQuery,
    SearchEventDatesQuery,
)
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.query_bus import QueryBus
from project.container import Application
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.event_date_mapping import (
    description_preview,
    photo_of,
)
from project.presentation.bff.public.schemas import (
    WidgetCategory,
    WidgetCategoryList,
    WidgetEvent,
    WidgetEventDate,
    WidgetEventDatePage,
    WidgetEventDateParams,
)
from project.presentation.bff.routing import bff_route
from project.shared.dateutils import form_input_to_date
from project.shared.utils import get_event_category_name


def _to_widget_date(hit) -> WidgetEventDate:
    event = hit.event
    return WidgetEventDate(
        id=hit.id,
        start=hit.start,
        end=hit.end,
        allday=hit.allday,
        event=WidgetEvent(
            id=event.id,
            name=event.name,
            description_preview=description_preview(event.description),
            status=event.status.name if event.status else None,
            public_status=event.public_status.name,
            booked_up=event.booked_up,
            attendance_mode=(
                event.attendance_mode.name if event.attendance_mode else None
            ),
            organization_name=event.admin_unit.name,
            organizer_name=event.organizer.name if event.organizer else None,
            place_name=event.event_place.name if event.event_place else None,
            photo=photo_of(event.photo),
        ),
    )


@bff_route(
    bff_public_bp,
    "/widget/event-dates",
    query=WidgetEventDateParams,
    response=WidgetEventDatePage,
    summary="Event dates for the embedded widgets",
)
@inject
def list_widget_event_dates(
    query: WidgetEventDateParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    criteria = EventSearchCriteria(
        date_from=form_input_to_date(query.date_from.isoformat()),
        date_to=(
            form_input_to_date(query.date_to.isoformat(), 23, 59, 59)
            if query.date_to
            else None
        ),
        keyword=(query.keyword or "").strip() or None,
        category_ids=[c for c in query.category_id if c > 0],
        admin_unit_id=query.organization_id,
        include_planned=True,
        include_admin_unit_references=True,
    )
    page = query_bus.handle(
        SearchEventDatesQuery(criteria=criteria, page=query.to_page_request())
    )
    return WidgetEventDatePage(
        items=[_to_widget_date(h) for h in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
    )


@bff_route(
    bff_public_bp,
    "/widget/categories",
    response=WidgetCategoryList,
    summary="Event categories for the embedded widgets",
)
@inject
def list_widget_categories(
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    categories = query_bus.handle(ListAllEventCategoriesQuery())
    return WidgetCategoryList(
        items=sorted(
            [
                WidgetCategory(id=c.id, name=str(get_event_category_name(c)))
                for c in categories
            ],
            key=lambda c: c.name,
        )
    )
